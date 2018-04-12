import tensorflow as tf
import utils


def focal_sigmoid_cross_entropy_with_logits(
        labels,
        logits,
        focus=2.0,
        alpha=0.25,
        name='focal_sigmoid_cross_entropy_with_logits'):
    with tf.name_scope(name):
        alpha = tf.ones_like(labels) * alpha
        labels_eq_1 = tf.equal(labels, 1)

        loss = tf.nn.sigmoid_cross_entropy_with_logits(
            labels=labels, logits=logits)
        prob = tf.nn.sigmoid(logits)
        a_balance = tf.where(labels_eq_1, alpha, 1 - alpha)
        prob_true = tf.where(labels_eq_1, prob, 1 - prob)
        modulating_factor = (1.0 - prob_true)**focus

        return a_balance * modulating_factor * loss


def safe_div(numerator, denominator):
    return tf.where(tf.greater(denominator, 0),
                    tf.div(numerator, tf.where(tf.equal(denominator, 0), tf.ones_like(denominator), denominator)),
                    tf.zeros_like(numerator))


def classification_loss(labels, logits, non_background_mask):
    class_loss = focal_sigmoid_cross_entropy_with_logits(
        labels=labels, logits=logits)
    class_loss = safe_div(tf.reduce_sum(class_loss), tf.reduce_sum(tf.to_float(non_background_mask)))

    return class_loss


# def regression_loss(labels, logits, non_background_mask):
#     regr_loss = tf.losses.huber_loss(
#         labels=labels,
#         predictions=logits,
#         weights=tf.expand_dims(non_background_mask, -1),
#         reduction=tf.losses.Reduction.SUM_BY_NONZERO_WEIGHTS)
#
#     return regr_loss

def regression_loss(labels, logits, non_background_mask):
    regr_loss = tf.log(tf.cosh(labels - logits))
    regr_loss = tf.boolean_mask(regr_loss, non_background_mask)
    regr_loss = safe_div(tf.reduce_sum(regr_loss), tf.reduce_sum(tf.to_float(non_background_mask)))

    return regr_loss


def loss(labels, logits, name='loss'):
    with tf.name_scope(name):
        labels = tuple(utils.merge_outputs(x) for x in labels)
        logits = tuple(utils.merge_outputs(x) for x in logits)

        class_labels, regr_labels = labels
        class_logits, regr_logits = logits

        non_background_mask = tf.not_equal(tf.argmax(class_labels, -1), 0)

        class_loss = classification_loss(
            labels=class_labels,
            logits=class_logits,
            non_background_mask=non_background_mask)
        regr_loss = regression_loss(
            labels=regr_labels,
            logits=regr_logits,
            non_background_mask=non_background_mask)

        return class_loss, regr_loss
