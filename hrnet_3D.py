import keras.backend as K
from keras.models import Model
from keras.layers import Input, Conv3D, BatchNormalization, Activation
from keras.layers import UpSampling3D, add, concatenate


def convP3D(x, out_filters, strides=(1,1,1)):
    x = Conv3D(out_filters,kernel_size=(1,1,1),padding = 'same')(x)
    x = Conv3D(out_filters/4, kernel_size=(1,3,3), padding='same', strides=strides, use_bias=False, kernel_initializer='he_normal')(x)
    x = Conv3D(out_filters/4, kernel_size=(3,1,1), padding='same', strides=(1,1,1), use_bias=False, kernel_initializer='he_normal')(x)
    x = Conv3D(out_filters,kernel_size=(1,1,1),padding = 'same')(x)
    return x


def basic_Block(input, out_filters, strides=(1,1,1), with_conv_shortcut=False):
    x = Conv3D(out_filters, kernel_size=(3,3,3),padding = 'same')(input)
#    x = Conv3D(out_filters, kernel_size=(3,1,1),padding = 'same')(x)

    x = BatchNormalization(axis=-1)(x)
    x = Activation('relu')(x)

    x = Conv3D(out_filters,kernel_size=(3,3,3),padding = 'same')(x)
#    x = Conv3D(out_filters,kernel_size=(3,1,1),padding = 'same')(x)

    x = BatchNormalization(axis=-1)(x)

    if with_conv_shortcut:
        residual = Conv3D(out_filters, kernel_size=(1,1,1), strides=strides, use_bias=False, kernel_initializer='he_normal')(input)
        residual = BatchNormalization(axis=-1)(residual)
        x = add([x, residual])
    else:
        x = add([x, input])

    x = Activation('relu')(x)
    return x


def bottleneck_Block(input, out_filters, strides=(1,1,1), with_conv_shortcut=False):
    expansion = 4
    de_filters = int(out_filters / expansion)

    x = Conv3D(de_filters, kernel_size=(1,1,1), use_bias=False, kernel_initializer='he_normal')(input)
    x = BatchNormalization(axis=-1)(x)
    x = Activation('relu')(x)

    x = Conv3D(de_filters, kernel_size=(3,3,3),padding = 'same')(x)
#    x = Conv3D(de_filters, kernel_size=(3,1,1),padding = 'same')(x)

    x = BatchNormalization(axis=-1)(x)
    x = Activation('relu')(x)

    x = Conv3D(out_filters, kernel_size=(1,1,1), use_bias=False, kernel_initializer='he_normal')(x)
    x = BatchNormalization(axis=-1)(x)

    if with_conv_shortcut:
        residual = Conv3D(out_filters, kernel_size=(1,1,1), strides=strides, use_bias=False, kernel_initializer='he_normal')(input)
        residual = BatchNormalization(axis=-1)(residual)
        x = add([x, residual])
    else:
        x = add([x, input])

    x = Activation('relu')(x)
    return x


def stem_net(input):
    x = Conv3D(64, kernel_size=(3,3,3),padding='same')(input)
    x = BatchNormalization(axis=-1)(x)
    x = Activation('relu')(x)

    x = bottleneck_Block(x, 256, with_conv_shortcut=True)
    x = bottleneck_Block(x, 256, with_conv_shortcut=False)
    x = bottleneck_Block(x, 256, with_conv_shortcut=False)
    x = bottleneck_Block(x, 256, with_conv_shortcut=False)

    return x


def transition_layer1(x, out_filters_list=[32, 64]):
    x0 = Conv3D(out_filters_list[0], kernel_size=(1,3,3), padding='same', use_bias=False, kernel_initializer='he_normal')(x)
    x0 = BatchNormalization(axis=-1)(x0)
    x0 = Activation('relu')(x0)

    x1 = Conv3D(out_filters_list[1], kernel_size=(1,3,3), strides=(1,2,2), padding='same', use_bias=False, kernel_initializer='he_normal')(x)
    x1 = BatchNormalization(axis=-1)(x1)
    x1 = Activation('relu')(x1)
    return [x0, x1]


def make_branch1_0(x, out_filters=32):
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    return x


def make_branch1_1(x, out_filters=64):
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    return x


def fuse_layer1(x):
    x0_0 = x[0]
    x0_1 = Conv3D(32, kernel_size=(1,1,1), use_bias=False, kernel_initializer='he_normal')(x[1])
    x0_1 = BatchNormalization(axis=-1)(x0_1)
    x0_1 = UpSampling3D(size=(1,2,2))(x0_1)
    x0 = add([x0_0, x0_1])

    x1_0 = Conv3D(64, kernel_size=(1,3,3), strides=(1,2,2), padding='same', use_bias=False, kernel_initializer='he_normal')(x[0])
    x1_0 = BatchNormalization(axis=-1)(x1_0)
    x1_1 = x[1]
    x1 = add([x1_0, x1_1])
    return [x0, x1]


def transition_layer2(x, out_filters_list=[32, 64, 128]):
    x0 = Conv3D(out_filters_list[0], kernel_size=(1,3,3), padding='same', use_bias=False, kernel_initializer='he_normal')(x[0])
    x0 = BatchNormalization(axis=-1)(x0)
    x0 = Activation('relu')(x0)

    x1 = Conv3D(out_filters_list[1], kernel_size=(1,3,3), padding='same', use_bias=False, kernel_initializer='he_normal')(x[1])
    x1 = BatchNormalization(axis=-1)(x1)
    x1 = Activation('relu')(x1)

    x2 = Conv3D(out_filters_list[2], kernel_size=(1,3,3), strides=(1,2,2), padding='same', use_bias=False, kernel_initializer='he_normal')(x[1])
    x2 = BatchNormalization(axis=-1)(x2)
    x2 = Activation('relu')(x2)
    return [x0, x1, x2]


def make_branch2_0(x, out_filters=32):
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    return x


def make_branch2_1(x, out_filters=64):
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    return x


def make_branch2_2(x, out_filters=128):
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    return x


def fuse_layer2(x):
    x0_0 = x[0]
    x0_1 = Conv3D(32, kernel_size=(1,1,1), use_bias=False, kernel_initializer='he_normal')(x[1])
    x0_1 = BatchNormalization(axis=-1)(x0_1)
    x0_1 = UpSampling3D(size=(1,2,2))(x0_1)
    x0_2 = Conv3D(32, kernel_size=(1,1,1), use_bias=False, kernel_initializer='he_normal')(x[2])
    x0_2 = BatchNormalization(axis=-1)(x0_2)
    x0_2 = UpSampling3D(size=(1,4,4))(x0_2)
    x0 = add([x0_0, x0_1, x0_2])

    x1_0 = Conv3D(64, kernel_size=(1,3,3), strides=(1,2,2), padding='same', use_bias=False, kernel_initializer='he_normal')(x[0])
    x1_0 = BatchNormalization(axis=-1)(x1_0)
    x1_1 = x[1]
    x1_2 = Conv3D(64, kernel_size=(1,1,1), use_bias=False, kernel_initializer='he_normal')(x[2])
    x1_2 = BatchNormalization(axis=-1)(x1_2)
    x1_2 = UpSampling3D(size=(1,2,2))(x1_2)
    x1 = add([x1_0, x1_1, x1_2])

    x2_0 = Conv3D(32, kernel_size=(1,3,3), strides=(1,2,2), padding='same', use_bias=False, kernel_initializer='he_normal')(x[0])
    x2_0 = BatchNormalization(axis=-1)(x2_0)
    x2_0 = Activation('relu')(x2_0)
    x2_0 = Conv3D(128, kernel_size=(1,3,3), strides=(1,2,2), padding='same', use_bias=False, kernel_initializer='he_normal')(x2_0)
    x2_0 = BatchNormalization(axis=-1)(x2_0)
    x2_1 = Conv3D(128, kernel_size=(1,3,3), strides=(1,2,2), padding='same', use_bias=False, kernel_initializer='he_normal')(x[1])
    x2_1 = BatchNormalization(axis=-1)(x2_1)
    x2_2 = x[2]
    x2 = add([x2_0, x2_1, x2_2])
    return [x0, x1, x2]


def transition_layer3(x, out_filters_list=[32, 64, 128, 256]):
    x0 = Conv3D(out_filters_list[0], kernel_size=(1,3,3), padding='same', use_bias=False, kernel_initializer='he_normal')(x[0])
    x0 = BatchNormalization(axis=-1)(x0)
    x0 = Activation('relu')(x0)

    x1 = Conv3D(out_filters_list[1], kernel_size=(1,3,3), padding='same', use_bias=False, kernel_initializer='he_normal')(x[1])
    x1 = BatchNormalization(axis=-1)(x1)
    x1 = Activation('relu')(x1)

    x2 = Conv3D(out_filters_list[2], kernel_size=(1,3,3), padding='same', use_bias=False, kernel_initializer='he_normal')(x[2])
    x2 = BatchNormalization(axis=-1)(x2)
    x2 = Activation('relu')(x2)

    x3 = Conv3D(out_filters_list[3], kernel_size=(1,3,3), strides=(1,2,2),padding='same', use_bias=False, kernel_initializer='he_normal')(x[2])
    x3 = BatchNormalization(axis=-1)(x3)
    x3 = Activation('relu')(x3)
    return [x0, x1, x2, x3]


def make_branch3_0(x, out_filters=32):
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    return x


def make_branch3_1(x, out_filters=64):
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    return x


def make_branch3_2(x, out_filters=128):
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    return x


def make_branch3_3(x, out_filters=256):
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    x = basic_Block(x, out_filters, with_conv_shortcut=False)
    return x


def fuse_layer3(x):
    x0_0 = x[0]
    x0_1 = Conv3D(32, kernel_size=(1,1,1), use_bias=False, kernel_initializer='he_normal')(x[1])
    x0_1 = BatchNormalization(axis=-1)(x0_1)
    x0_1 = UpSampling3D(size=(1,2,2))(x0_1)
    x0_2 = Conv3D(32, kernel_size=(1,1,1), use_bias=False, kernel_initializer='he_normal')(x[2])
    x0_2 = BatchNormalization(axis=-1)(x0_2)
    x0_2 = UpSampling3D(size=(1,4,4))(x0_2)
    x0_3 = Conv3D(32, kernel_size=(1,1,1), use_bias=False, kernel_initializer='he_normal')(x[3])
    x0_3 = BatchNormalization(axis=-1)(x0_3)
    x0_3 = UpSampling3D(size=(1,8,8))(x0_3)
    x0 = concatenate([x0_0, x0_1])  #axis=-1
    return x0


def final_layer(x, classes=1):
    x = BatchNormalization(axis=-1)(x) # added this line and it worked magically ¯\_(ツ)_/¯
    x = UpSampling3D(size=(1,1,1))(x)
    x = Conv3D(classes, kernel_size=(1,1,1), use_bias=False, kernel_initializer='he_normal')(x)
    x = BatchNormalization(axis=-1)(x)
    x = Activation('relu', name='Classification')(x)
    return x


def HRnet(batch_size, depth, height, width, channel, classes):
    # inputs = Input(batch_shape=(batch_size,) + (height, width, channel))
    inputs = Input(shape=(depth,height,width,channel))
    x = stem_net(inputs)

    x = transition_layer1(x)
    x0 = make_branch1_0(x[0])
    x1 = make_branch1_1(x[1])

    x = fuse_layer1([x0, x1])


    x = transition_layer2(x)
    x0 = make_branch2_0(x[0])
    x1 = make_branch2_1(x[1])
    x2 = make_branch2_2(x[2])
    x = fuse_layer2([x0, x1, x2])


    x = transition_layer3(x)
    x0 = make_branch3_0(x[0])
    x1 = make_branch3_1(x[1])
    x2 = make_branch3_2(x[2])
    x3 = make_branch3_3(x[3])
    x = fuse_layer3([x0, x1, x2, x3])

    out = final_layer(x, classes=classes)

    model = Model(inputs=inputs, outputs=out)

    return model


# from keras.utils import plot_model
# import os
# os.environ["PATH"] += os.pathsep + 'C:/Program Files (x86)/Graphviz2.38/bin/'
#
# model = seg_hrnet(batch_size=2, height=512, width=512, channel=3, classes=1)
# model.summary()
# plot_model(model, to_file='seg_hrnet.png', show_shapes=True)
