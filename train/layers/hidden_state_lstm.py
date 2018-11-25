from keras import backend as K
from keras.layers.recurrent import LSTM

class HiddenStateLSTM(LSTM):
    """LSTM with input/output capabilities for its hidden state.
    This layer behaves just like an LSTM, except that it accepts further inputs
    to be used as its initial states, and returns additional outputs,
    representing the layer's final states.
    See Also:
        https://github.com/fchollet/keras/issues/2995
    """
    def build(self, input_shape):
        if isinstance(input_shape, list) and len(input_shape) > 1:
            input_shape, *hidden_shapes = input_shape
            for shape in hidden_shapes:
                assert shape[0]  == input_shape[0]
                assert shape[-1] == self.units

        super().build(input_shape)

    def call(self, x, mask=None, constants=None, **kwargs):
        # input shape: (nb_samples, time (padded with zeros), input_dim)
        input_shape = self.input_spec[0].shape
        if isinstance(x, (tuple, list)):
            x, *custom_initial = x
        else:
            custom_initial = None

        if custom_initial:
            initial_states = custom_initial
        elif self.stateful:
            initial_states = self.states
        else:
            initial_states = self.get_initial_states(x)

        preprocessed_input = x # self.preprocess_input(x)

        # only use the main input mask
        if isinstance(mask, list):
            mask = mask[0]

        last_output, outputs, states = K.rnn(self.step, preprocessed_input,
                initial_states,
                go_backwards=self.go_backwards,
                mask=mask,
                constants=constants,
                unroll=self.unroll,
                input_length=input_shape[1]
            )

        if self.return_sequences:
            return [outputs, *states]
        else:
            return [last_output, *states]


    def step(self, x, states):
        h_tm1 = states[0]
        c_tm1 = states[1]

        x_i = K.dot(x, self.cell.kernel_i) + self.cell.bias_i
        x_f = K.dot(x, self.cell.kernel_f) + self.cell.bias_f
        x_c = K.dot(x, self.cell.kernel_c) + self.cell.bias_c
        x_o = K.dot(x, self.cell.kernel_o) + self.cell.bias_o

        i = self.cell.recurrent_activation(x_i + K.dot(h_tm1, self.cell.recurrent_kernel_i))
        f = self.cell.recurrent_activation(x_f + K.dot(h_tm1, self.cell.recurrent_kernel_f))
        c = f * c_tm1 + i * self.cell.activation(x_c + K.dot(h_tm1, self.cell.recurrent_kernel_c))
        o = self.cell.recurrent_activation(x_o + K.dot(h_tm1, self.cell.recurrent_kernel_o))

        h = o * self.activation(c)
        return h, [h, c]

    def compute_output_shape(self, input_shape):
        if isinstance(input_shape, list) and len(input_shape) > 1:
            input_shape = input_shape[0]
        if self.return_sequences:
            output_shape = (input_shape[0], input_shape[1], self.units)
        else:
            output_shape = (input_shape[0], self.units)
        state_output = (input_shape[0], self.units)
        return [output_shape, state_output, state_output]

    def compute_mask(self, input, mask):
        if isinstance(mask, list) and len(mask) > 1:
            return mask
        elif self.return_sequences:
            return [mask, None, None]
        else:
            return [None] * 3
