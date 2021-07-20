import tensorflow as tf
from tensorflow_probability import distributions as tfd

from phat.learn.utils import GraphicMixin


def mon_mean(y, y_):
    mu, sigma = tf.unstack(y_, num=2, axis=-1)
    return tf.keras.backend.mean(mu)

def mon_std(y, y_):
    mu, sigma = tf.unstack(y_, num=2, axis=-1)
    return tf.keras.backend.mean(sigma)

def gnll_loss(y, y_):
    """ Computes the mean negative log-likelihood loss of y given the mixture parameters.
    """
    mu, sigma = tf.unstack(y_, num=2, axis=-1)
    dist = tfd.Normal(mu, sigma)
    return tf.reduce_mean(-dist.log_prob(y))

class DN(tf.keras.Model, GraphicMixin):
    def __init__(self, neurons=200):
        super(DN, self).__init__(name="DN")
        self.neurons = neurons
        
        self.h1 = tf.keras.layers.Dense(neurons, activation="relu", name="h1")
        self.h2 = tf.keras.layers.Dense(neurons//2, activation="relu", name="h2")
        self.h3 = tf.keras.layers.Dense(12, activation="relu", name="h3")
        
        self.mu = tf.keras.layers.Dense(1, name="mu")
        self.sigma = tf.keras.layers.Dense(1, activation="nnelu", name="sigma")
        self.pvec = tf.keras.layers.Concatenate(name="pvec")

    def call(self, inputs):
        x = self.h1(inputs)
        x = self.h2(x)
        x = self.h3(x)
        
        mu_v = self.mu(x)
        sigma_v = self.sigma(x)

        return self.pvec([mu_v, sigma_v])
