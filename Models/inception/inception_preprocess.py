from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import tensorflow.contrib.slim as slim
import tensorflow.contrib.slim.nets as nets
import os
import numpy as np

# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Contains the definition of the Inception V4 architecture.

As described in http://arxiv.org/abs/1602.07261.

  Inception-v4, Inception-ResNet and the Impact of Residual Connections
    on Learning
  Christian Szegedy, Sergey Ioffe, Vincent Vanhoucke, Alex Alemi
"""

slim = tf.contrib.slim

######## INCPETION UTILS ########
def inception_arg_scope(weight_decay=0.00004,
                        use_batch_norm=True,
                        batch_norm_decay=0.9997,
                        batch_norm_epsilon=0.001,
                        activation_fn=tf.nn.relu):
  """Defines the default arg scope for inception models.
  Args:
    weight_decay: The weight decay to use for regularizing the model.
    use_batch_norm: "If `True`, batch_norm is applied after each convolution.
    batch_norm_decay: Decay for batch norm moving average.
    batch_norm_epsilon: Small float added to variance to avoid dividing by zero
      in batch norm.
    activation_fn: Activation function for conv2d.
  Returns:
    An `arg_scope` to use for the inception models.
  """
  batch_norm_params = {
      # Decay for the moving averages.
      'decay': batch_norm_decay,
      # epsilon to prevent 0s in variance.
      'epsilon': batch_norm_epsilon,
      # collection containing update_ops.
      'updates_collections': tf.GraphKeys.UPDATE_OPS,
      # use fused batch norm if possible.
      'fused': None,
  }
  if use_batch_norm:
    normalizer_fn = slim.batch_norm
    normalizer_params = batch_norm_params
  else:
    normalizer_fn = None
    normalizer_params = {}
  # Set weight_decay for weights in Conv and FC layers.
  with slim.arg_scope([slim.conv2d, slim.fully_connected],
                      weights_regularizer=slim.l2_regularizer(weight_decay)):
    with slim.arg_scope(
        [slim.conv2d],
        weights_initializer=slim.variance_scaling_initializer(),
        activation_fn=activation_fn,
        normalizer_fn=normalizer_fn,
        normalizer_params=normalizer_params) as sc:
      return sc

#############

def block_inception_a(inputs, scope=None, reuse=None):
  """Builds Inception-A block for Inception v4 network."""
  # By default use stride=1 and SAME padding
  with slim.arg_scope([slim.conv2d, slim.avg_pool2d, slim.max_pool2d],
                      stride=1, padding='SAME'):
    with tf.variable_scope(scope, 'BlockInceptionA', [inputs], reuse=reuse):
      with tf.variable_scope('Branch_0'):
        branch_0 = slim.conv2d(inputs, 96, [1, 1], scope='Conv2d_0a_1x1')
      with tf.variable_scope('Branch_1'):
        branch_1 = slim.conv2d(inputs, 64, [1, 1], scope='Conv2d_0a_1x1')
        branch_1 = slim.conv2d(branch_1, 96, [3, 3], scope='Conv2d_0b_3x3')
      with tf.variable_scope('Branch_2'):
        branch_2 = slim.conv2d(inputs, 64, [1, 1], scope='Conv2d_0a_1x1')
        branch_2 = slim.conv2d(branch_2, 96, [3, 3], scope='Conv2d_0b_3x3')
        branch_2 = slim.conv2d(branch_2, 96, [3, 3], scope='Conv2d_0c_3x3')
      with tf.variable_scope('Branch_3'):
        branch_3 = slim.avg_pool2d(inputs, [3, 3], scope='AvgPool_0a_3x3')
        branch_3 = slim.conv2d(branch_3, 96, [1, 1], scope='Conv2d_0b_1x1')
      return tf.concat(axis=3, values=[branch_0, branch_1, branch_2, branch_3])


def block_reduction_a(inputs, scope=None, reuse=None):
  """Builds Reduction-A block for Inception v4 network."""
  # By default use stride=1 and SAME padding
  with slim.arg_scope([slim.conv2d, slim.avg_pool2d, slim.max_pool2d],
                      stride=1, padding='SAME'):
    with tf.variable_scope(scope, 'BlockReductionA', [inputs], reuse=reuse):
      with tf.variable_scope('Branch_0'):
        branch_0 = slim.conv2d(inputs, 384, [3, 3], stride=2, padding='VALID',
                               scope='Conv2d_1a_3x3')
      with tf.variable_scope('Branch_1'):
        branch_1 = slim.conv2d(inputs, 192, [1, 1], scope='Conv2d_0a_1x1')
        branch_1 = slim.conv2d(branch_1, 224, [3, 3], scope='Conv2d_0b_3x3')
        branch_1 = slim.conv2d(branch_1, 256, [3, 3], stride=2,
                               padding='VALID', scope='Conv2d_1a_3x3')
      with tf.variable_scope('Branch_2'):
        branch_2 = slim.max_pool2d(inputs, [3, 3], stride=2, padding='VALID',
                                   scope='MaxPool_1a_3x3')
      return tf.concat(axis=3, values=[branch_0, branch_1, branch_2])


def block_inception_b(inputs, scope=None, reuse=None):
  """Builds Inception-B block for Inception v4 network."""
  # By default use stride=1 and SAME padding
  with slim.arg_scope([slim.conv2d, slim.avg_pool2d, slim.max_pool2d],
                      stride=1, padding='SAME'):
    with tf.variable_scope(scope, 'BlockInceptionB', [inputs], reuse=reuse):
      with tf.variable_scope('Branch_0'):
        branch_0 = slim.conv2d(inputs, 384, [1, 1], scope='Conv2d_0a_1x1')
      with tf.variable_scope('Branch_1'):
        branch_1 = slim.conv2d(inputs, 192, [1, 1], scope='Conv2d_0a_1x1')
        branch_1 = slim.conv2d(branch_1, 224, [1, 7], scope='Conv2d_0b_1x7')
        branch_1 = slim.conv2d(branch_1, 256, [7, 1], scope='Conv2d_0c_7x1')
      with tf.variable_scope('Branch_2'):
        branch_2 = slim.conv2d(inputs, 192, [1, 1], scope='Conv2d_0a_1x1')
        branch_2 = slim.conv2d(branch_2, 192, [7, 1], scope='Conv2d_0b_7x1')
        branch_2 = slim.conv2d(branch_2, 224, [1, 7], scope='Conv2d_0c_1x7')
        branch_2 = slim.conv2d(branch_2, 224, [7, 1], scope='Conv2d_0d_7x1')
        branch_2 = slim.conv2d(branch_2, 256, [1, 7], scope='Conv2d_0e_1x7')
      with tf.variable_scope('Branch_3'):
        branch_3 = slim.avg_pool2d(inputs, [3, 3], scope='AvgPool_0a_3x3')
        branch_3 = slim.conv2d(branch_3, 128, [1, 1], scope='Conv2d_0b_1x1')
      return tf.concat(axis=3, values=[branch_0, branch_1, branch_2, branch_3])


def block_reduction_b(inputs, scope=None, reuse=None):
  """Builds Reduction-B block for Inception v4 network."""
  # By default use stride=1 and SAME padding
  with slim.arg_scope([slim.conv2d, slim.avg_pool2d, slim.max_pool2d],
                      stride=1, padding='SAME'):
    with tf.variable_scope(scope, 'BlockReductionB', [inputs], reuse=reuse):
      with tf.variable_scope('Branch_0'):
        branch_0 = slim.conv2d(inputs, 192, [1, 1], scope='Conv2d_0a_1x1')
        branch_0 = slim.conv2d(branch_0, 192, [3, 3], stride=2,
                               padding='VALID', scope='Conv2d_1a_3x3')
      with tf.variable_scope('Branch_1'):
        branch_1 = slim.conv2d(inputs, 256, [1, 1], scope='Conv2d_0a_1x1')
        branch_1 = slim.conv2d(branch_1, 256, [1, 7], scope='Conv2d_0b_1x7')
        branch_1 = slim.conv2d(branch_1, 320, [7, 1], scope='Conv2d_0c_7x1')
        branch_1 = slim.conv2d(branch_1, 320, [3, 3], stride=2,
                               padding='VALID', scope='Conv2d_1a_3x3')
      with tf.variable_scope('Branch_2'):
        branch_2 = slim.max_pool2d(inputs, [3, 3], stride=2, padding='VALID',
                                   scope='MaxPool_1a_3x3')
      return tf.concat(axis=3, values=[branch_0, branch_1, branch_2])


def block_inception_c(inputs, scope=None, reuse=None):
  """Builds Inception-C block for Inception v4 network."""
  # By default use stride=1 and SAME padding
  with slim.arg_scope([slim.conv2d, slim.avg_pool2d, slim.max_pool2d],
                      stride=1, padding='SAME'):
    with tf.variable_scope(scope, 'BlockInceptionC', [inputs], reuse=reuse):
      with tf.variable_scope('Branch_0'):
        branch_0 = slim.conv2d(inputs, 256, [1, 1], scope='Conv2d_0a_1x1')
      with tf.variable_scope('Branch_1'):
        branch_1 = slim.conv2d(inputs, 384, [1, 1], scope='Conv2d_0a_1x1')
        branch_1 = tf.concat(axis=3, values=[
            slim.conv2d(branch_1, 256, [1, 3], scope='Conv2d_0b_1x3'),
            slim.conv2d(branch_1, 256, [3, 1], scope='Conv2d_0c_3x1')])
      with tf.variable_scope('Branch_2'):
        branch_2 = slim.conv2d(inputs, 384, [1, 1], scope='Conv2d_0a_1x1')
        branch_2 = slim.conv2d(branch_2, 448, [3, 1], scope='Conv2d_0b_3x1')
        branch_2 = slim.conv2d(branch_2, 512, [1, 3], scope='Conv2d_0c_1x3')
        branch_2 = tf.concat(axis=3, values=[
            slim.conv2d(branch_2, 256, [1, 3], scope='Conv2d_0d_1x3'),
            slim.conv2d(branch_2, 256, [3, 1], scope='Conv2d_0e_3x1')])
      with tf.variable_scope('Branch_3'):
        branch_3 = slim.avg_pool2d(inputs, [3, 3], scope='AvgPool_0a_3x3')
        branch_3 = slim.conv2d(branch_3, 256, [1, 1], scope='Conv2d_0b_1x1')
      return tf.concat(axis=3, values=[branch_0, branch_1, branch_2, branch_3])


def inception_v4_base(inputs, final_endpoint='Mixed_7d', scope=None):
  """Creates the Inception V4 network up to the given final endpoint.

  Args:
    inputs: a 4-D tensor of size [batch_size, height, width, 3].
    final_endpoint: specifies the endpoint to construct the network up to.
      It can be one of [ 'Conv2d_1a_3x3', 'Conv2d_2a_3x3', 'Conv2d_2b_3x3',
      'Mixed_3a', 'Mixed_4a', 'Mixed_5a', 'Mixed_5b', 'Mixed_5c', 'Mixed_5d',
      'Mixed_5e', 'Mixed_6a', 'Mixed_6b', 'Mixed_6c', 'Mixed_6d', 'Mixed_6e',
      'Mixed_6f', 'Mixed_6g', 'Mixed_6h', 'Mixed_7a', 'Mixed_7b', 'Mixed_7c',
      'Mixed_7d']
    scope: Optional variable_scope.

  Returns:
    logits: the logits outputs of the model.
    end_points: the set of end_points from the inception model.

  Raises:
    ValueError: if final_endpoint is not set to one of the predefined values,
  """
  end_points = {}

  def add_and_check_final(name, net):
    end_points[name] = net
    return name == final_endpoint

  with tf.variable_scope(scope, 'InceptionV4', [inputs]):
    with slim.arg_scope([slim.conv2d, slim.max_pool2d, slim.avg_pool2d],
                        stride=1, padding='SAME'):
      # 299 x 299 x 3
      net = slim.conv2d(inputs, 32, [3, 3], stride=2,
                        padding='VALID', scope='Conv2d_1a_3x3')
      if add_and_check_final('Conv2d_1a_3x3', net): return net, end_points
      # 149 x 149 x 32
      net = slim.conv2d(net, 32, [3, 3], padding='VALID',
                        scope='Conv2d_2a_3x3')
      if add_and_check_final('Conv2d_2a_3x3', net): return net, end_points
      # 147 x 147 x 32
      net = slim.conv2d(net, 64, [3, 3], scope='Conv2d_2b_3x3')
      if add_and_check_final('Conv2d_2b_3x3', net): return net, end_points
      # 147 x 147 x 64
      with tf.variable_scope('Mixed_3a'):
        with tf.variable_scope('Branch_0'):
          branch_0 = slim.max_pool2d(net, [3, 3], stride=2, padding='VALID',
                                     scope='MaxPool_0a_3x3')
        with tf.variable_scope('Branch_1'):
          branch_1 = slim.conv2d(net, 96, [3, 3], stride=2, padding='VALID',
                                 scope='Conv2d_0a_3x3')
        net = tf.concat(axis=3, values=[branch_0, branch_1])
        if add_and_check_final('Mixed_3a', net): return net, end_points

      # 73 x 73 x 160
      with tf.variable_scope('Mixed_4a'):
        with tf.variable_scope('Branch_0'):
          branch_0 = slim.conv2d(net, 64, [1, 1], scope='Conv2d_0a_1x1')
          branch_0 = slim.conv2d(branch_0, 96, [3, 3], padding='VALID',
                                 scope='Conv2d_1a_3x3')
        with tf.variable_scope('Branch_1'):
          branch_1 = slim.conv2d(net, 64, [1, 1], scope='Conv2d_0a_1x1')
          branch_1 = slim.conv2d(branch_1, 64, [1, 7], scope='Conv2d_0b_1x7')
          branch_1 = slim.conv2d(branch_1, 64, [7, 1], scope='Conv2d_0c_7x1')
          branch_1 = slim.conv2d(branch_1, 96, [3, 3], padding='VALID',
                                 scope='Conv2d_1a_3x3')
        net = tf.concat(axis=3, values=[branch_0, branch_1])
        if add_and_check_final('Mixed_4a', net): return net, end_points

      # 71 x 71 x 192
      with tf.variable_scope('Mixed_5a'):
        with tf.variable_scope('Branch_0'):
          branch_0 = slim.conv2d(net, 192, [3, 3], stride=2, padding='VALID',
                                 scope='Conv2d_1a_3x3')
        with tf.variable_scope('Branch_1'):
          branch_1 = slim.max_pool2d(net, [3, 3], stride=2, padding='VALID',
                                     scope='MaxPool_1a_3x3')
        net = tf.concat(axis=3, values=[branch_0, branch_1])
        if add_and_check_final('Mixed_5a', net): return net, end_points

      # 35 x 35 x 384
      # 4 x Inception-A blocks
      for idx in range(4):
        block_scope = 'Mixed_5' + chr(ord('b') + idx)
        net = block_inception_a(net, block_scope)
        if add_and_check_final(block_scope, net): return net, end_points

      # 35 x 35 x 384
      # Reduction-A block
      net = block_reduction_a(net, 'Mixed_6a')
      if add_and_check_final('Mixed_6a', net): return net, end_points

      # 17 x 17 x 1024
      # 7 x Inception-B blocks
      for idx in range(7):
        block_scope = 'Mixed_6' + chr(ord('b') + idx)
        net = block_inception_b(net, block_scope)
        if add_and_check_final(block_scope, net): return net, end_points

      # 17 x 17 x 1024
      # Reduction-B block
      net = block_reduction_b(net, 'Mixed_7a')
      if add_and_check_final('Mixed_7a', net): return net, end_points

      # 8 x 8 x 1536
      # 3 x Inception-C blocks
      for idx in range(3):
        block_scope = 'Mixed_7' + chr(ord('b') + idx)
        net = block_inception_c(net, block_scope)
        if add_and_check_final(block_scope, net): return net, end_points
  raise ValueError('Unknown final endpoint %s' % final_endpoint)


def inception_v4(inputs, num_classes=1001, is_training=True,
                 dropout_keep_prob=0.8,
                 reuse=None,
                 scope='InceptionV4',
                 create_aux_logits=True):
  """Creates the Inception V4 model.

  Args:
    inputs: a 4-D tensor of size [batch_size, height, width, 3].
    num_classes: number of predicted classes. If 0 or None, the logits layer
      is omitted and the input features to the logits layer (before dropout)
      are returned instead.
    is_training: whether is training or not.
    dropout_keep_prob: float, the fraction to keep before final layer.
    reuse: whether or not the network and its variables should be reused. To be
      able to reuse 'scope' must be given.
    scope: Optional variable_scope.
    create_aux_logits: Whether to include the auxiliary logits.

  Returns:
    net: a Tensor with the logits (pre-softmax activations) if num_classes
      is a non-zero integer, or the non-dropped input to the logits layer
      if num_classes is 0 or None.
    end_points: the set of end_points from the inception model.
  """
  end_points = {}
  with tf.variable_scope(scope, 'InceptionV4', [inputs], reuse=reuse) as scope:
    with slim.arg_scope([slim.batch_norm, slim.dropout],
                        is_training=is_training):
      net, end_points = inception_v4_base(inputs, scope=scope)

      with slim.arg_scope([slim.conv2d, slim.max_pool2d, slim.avg_pool2d],
                          stride=1, padding='SAME'):
        # Auxiliary Head logits
        if create_aux_logits and num_classes:
          with tf.variable_scope('AuxLogits'):
            # 17 x 17 x 1024
            aux_logits = end_points['Mixed_6h']
            aux_logits = slim.avg_pool2d(aux_logits, [5, 5], stride=3,
                                         padding='VALID',
                                         scope='AvgPool_1a_5x5')
            aux_logits = slim.conv2d(aux_logits, 128, [1, 1],
                                     scope='Conv2d_1b_1x1')
            aux_logits = slim.conv2d(aux_logits, 768,
                                     aux_logits.get_shape()[1:3],
                                     padding='VALID', scope='Conv2d_2a')
            aux_logits = slim.flatten(aux_logits)
            aux_logits = slim.fully_connected(aux_logits, num_classes,
                                              activation_fn=None,
                                              scope='Aux_logits')
            end_points['AuxLogits'] = aux_logits

        # Final pooling and prediction
        # TODO(sguada,arnoegw): Consider adding a parameter global_pool which
        # can be set to False to disable pooling here (as in resnet_*()).
        with tf.variable_scope('Logits'):
          # 8 x 8 x 1536
          kernel_size = net.get_shape()[1:3]
          if kernel_size.is_fully_defined():
            net = slim.avg_pool2d(net, kernel_size, padding='VALID',
                                  scope='AvgPool_1a')
          else:
            net = tf.reduce_mean(net, [1, 2], keep_dims=True,
                                 name='global_pool')
          end_points['global_pool'] = net
          if not num_classes:
            return net, end_points
          # 1 x 1 x 1536
          net = slim.dropout(net, dropout_keep_prob, scope='Dropout_1b')
          net = slim.flatten(net, scope='PreLogitsFlatten')
          end_points['PreLogitsFlatten'] = net
          # 1536
          logits = slim.fully_connected(net, num_classes, activation_fn=None,
                                        scope='Logits')
          end_points['Logits'] = logits
          end_points['Predictions'] = tf.nn.softmax(logits, name='Predictions')
    return logits, end_points
inception_v4.default_image_size = 299


inception_v4_arg_scope = inception_arg_scope



################
from os import listdir
from os.path import isfile, join

tf.reset_default_graph()

# Specify where the pretrained Model is saved.
model_path = 'inception_v4.ckpt'

# Specify where the new model will live
# log_dir = 'resnet_log/'

tf.reset_default_graph()

images = tf.placeholder(tf.float32, [None, 299, 299, 3])

with slim.arg_scope(inception_v4_arg_scope()):
    logits, end_points = inception_v4(images, is_training=False)

# check that the file path exists 
assert(os.path.isfile(model_path)) 

# create function to restore variables (can specify variables to exclude in get_variables_to_restore)
variables_to_restore = tf.contrib.framework.get_variables_to_restore()

# variable restorer 
restorer = tf.train.Saver(variables_to_restore)
# init function 
init = tf.initialize_all_variables()

# process image sample 
# files = [join("/home/ec2-user/Data/imagen_clean/", f) for f in listdir("/home/ec2-user/Data/imagen_clean/") if isfile(join("/home/ec2-user/Data/imagen_clean/", f))]
pie = "/home/ec2-user/Data/food-101/images/sushi"
files = [join(pie, f) for f in listdir(pie) if isfile(join(pie, f))]

# files = [join("/home/ec2-user/Data/dragonfly/img/", f) for f in listdir("/home/ec2-user/Data/dragonfly/img/") if isfile(join("/home/ec2-user/Data/dragonfly/img/", f))]
# can i even classify a dog?
# files = ["/home/ec2-user/Models/inception/dog_image.png"] # + files
# ties
# files = ["/home/ec2-user/Data/imagen_clean/n04591157_" + s + "_tie.jpg" for s in ["1774", "197", "2640", "4443"]]

legend = [None] * 1001
with open("./key.txt") as keyfile:
    for i in range(1, 1001):
        legend[i] = keyfile.readline()

filename_queue = tf.train.string_input_producer(files) #list of files to read

vectors = []

import csv
import gc

gc.enable()

cfg = tf.ConfigProto(intra_op_parallelism_threads=10)

with tf.Session(config=cfg) as sess, open('./sushi_prepool.csv', 'wb') as vfile:
    sess.run(init)
    restorer.restore(sess,model_path)
    tf.initialize_all_variables()
    # get layer before auxiliary logits pooling 
    pre_pool = end_points['Mixed_7d']

    # IMPORTANT!!!! Coordinate the loading of image files.
    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=sess, coord=coord)
    vectors = []

    # for outputting the vectors
    vec_writer = csv.writer(vfile)
 

    reader = tf.WholeFileReader()
    key, value = reader.read(filename_queue)
    image = tf.image.decode_jpeg(value)
    image = tf.image.convert_image_dtype(image, dtype=tf.float32)
    scaled_image_dog = tf.multiply(tf.subtract(image, 0.5), 2)
    image_shape = tf.shape(scaled_image_dog)
    n, m = image_shape[0], image_shape[1]
    s = tf.minimum(n, m)
    rn, rm = tf.subtract(n, s), tf.subtract(m, s)
    square_dog = tf.image.crop_to_bounding_box(scaled_image_dog, rn//2, rm//2, s, s)
    spliced_dog = tf.image.resize_images(square_dog, [299, 299])
    dog = tf.expand_dims(spliced_dog, axis = 0)

    for x in range(len(files)):
        print(x)
        '''
        # key, value = reader.read(filename_queue)
        if image.dtype != tf.float32:
            image = tf.image.convert_image_dtype(image, dtype=tf.float32) 
        scaled_image_dog = (sess.run(image) - 0.5) * 2
        n, m, rgb = scaled_image_dog.shape
        s = min(n, m)
        rn, rm = n - s, m - s
        square_dog = tf.image.crop_to_bounding_box(scaled_image_dog, rn//2, rm//2, s, s)
        spliced_dog = tf.image.resize_images(square_dog, [299, 299])
        input_dog = sess.run(spliced_dog)
        dog = np.expand_dims(input_dog, axis=0)
        '''
        input_dog = sess.run(dog)
        logits_out, pre_pool_out = sess.run([logits, pre_pool], {images: input_dog})
        print(key.eval()) # name of file
        print(pre_pool_out.shape)
        pre_pool_vector = pre_pool_out.ravel().tolist()
        vec_writer.writerow([key] + pre_pool_vector)
        print(legend[np.argmax(logits_out)])

    print("done!")
    # Finish off the filename queue coordinator.
    
    coord.request_stop()
    coord.join(threads)


    # evaluate on images_rand
    # print(pre_pool_out)
    # print(np.argmax(logits_out))
    print("model restored!")
