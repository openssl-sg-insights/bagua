import torch
import bagua_multihead_attn_raw_cuda
import bagua_self_multihead_attn_raw_cuda
import bagua_self_multihead_attn_cuda


class MultiheadAttnRawScoreFunc(torch.autograd.Function):
    @staticmethod
    def forward(ctx, heads, inputs_q, inputs_kv):
        heads_t = torch.tensor([heads])

        (outputs,) = bagua_multihead_attn_raw_cuda.forward(heads, inputs_q, inputs_kv)
        ctx.save_for_backward(heads_t, inputs_q, inputs_kv)
        return outputs

    @staticmethod
    def backward(ctx, output_grads):
        heads_t, inputs_q, inputs_kv = ctx.saved_tensors

        inputs_q_grads, inputs_kv_grads = bagua_multihead_attn_raw_cuda.backward(
            heads_t[0], output_grads, inputs_q, inputs_kv
        )

        return None, inputs_q_grads, inputs_kv_grads


class SelfMultiheadAttnRawScoreFunc(torch.autograd.Function):
    @staticmethod
    def forward(ctx, heads, inputs, coeff):
        heads_t = torch.tensor([heads])
        coeff_t = torch.tensor([coeff])

        (outputs,) = bagua_self_multihead_attn_raw_cuda.forward(heads, inputs, coeff)
        ctx.save_for_backward(heads_t, inputs, coeff_t)
        return outputs

    @staticmethod
    def backward(ctx, output_grads):
        heads_t, inputs, coeff_t = ctx.saved_tensors

        (inputs_grads,) = bagua_self_multihead_attn_raw_cuda.backward(
            heads_t[0], output_grads, inputs, coeff_t[0]
        )

        return None, inputs_grads


class SelfMultiheadAttnScoreFunc(torch.autograd.Function):
    @staticmethod
    def forward(ctx, heads, inputs, attention_mask, coeff, dropout):
        heads_t = torch.tensor([heads])
        coeff_t = torch.tensor([coeff])
        dropout_t = torch.tensor([dropout])
        use_mask = attention_mask is not None

        (
            softmax_results,
            dropout_results,
            dropout_mask,
            outputs,
        ) = bagua_self_multihead_attn_cuda.forward(
            use_mask, heads, inputs, attention_mask, coeff, dropout
        )
        ctx.save_for_backward(
            heads_t,
            inputs,
            softmax_results,
            dropout_results,
            dropout_mask,
            coeff_t,
            dropout_t,
        )
        return outputs

    @staticmethod
    def backward(ctx, output_grads):
        (
            heads_t,
            inputs,
            softmax_results,
            dropout_results,
            dropout_mask,
            coeff_t,
            dropout_t,
        ) = ctx.saved_tensors

        (inputs_grads,) = bagua_self_multihead_attn_cuda.backward(
            heads_t[0],
            output_grads,
            dropout_results,
            softmax_results,
            inputs,
            coeff_t[0],
            dropout_mask,
            dropout_t[0],
        )

        return None, inputs_grads
