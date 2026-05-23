import tensorflow as tf
import math

def build_model(num_classes=7, img_size=300):
    inputs = tf.keras.Input(shape=(img_size, img_size, 3))
    
    # Preprocessing expected by EfficientNet is included in the model itself 
    # for tf.keras.applications.EfficientNetB3 (it expects inputs in [0, 255])
    
    base_model = tf.keras.applications.EfficientNetB3(
        include_top=False,
        weights='imagenet',
        input_tensor=inputs
    )
    
    # Freeze the base model
    base_model.trainable = False
    
    x = base_model.output
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation='softmax', name='predictions')(x)
    
    model = tf.keras.Model(inputs, outputs, name="anal_fistula_detector")
    
    return model, base_model

def build_unet(img_size=300):
    def conv_block(inputs, filters):
        x = tf.keras.layers.Conv2D(filters, 3, padding="same")(inputs)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.Activation("relu")(x)
        x = tf.keras.layers.Conv2D(filters, 3, padding="same")(x)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.Activation("relu")(x)
        return x

    def encoder_block(inputs, filters):
        x = conv_block(inputs, filters)
        p = tf.keras.layers.MaxPooling2D((2, 2))(x)
        return x, p

    def decoder_block(inputs, skip_features, filters):
        x = tf.keras.layers.Conv2DTranspose(filters, (2, 2), strides=2, padding="same")(inputs)
        x = tf.keras.layers.Concatenate()([x, skip_features])
        x = conv_block(x, filters)
        return x

    inputs = tf.keras.Input(shape=(img_size, img_size, 3))
    
    # Calculate padding to make dimensions divisible by 16 (for 4 pooling layers)
    pad_total = math.ceil(img_size / 16) * 16 - img_size
    pad_top = pad_total // 2
    pad_bottom = pad_total - pad_top
    pad_left = pad_total // 2
    pad_right = pad_total - pad_left
    
    if pad_total > 0:
        x = tf.keras.layers.ZeroPadding2D(padding=((pad_top, pad_bottom), (pad_left, pad_right)))(inputs)
    else:
        x = inputs

    # Encoder
    s1, p1 = encoder_block(x, 64)
    s2, p2 = encoder_block(p1, 128)
    s3, p3 = encoder_block(p2, 256)
    s4, p4 = encoder_block(p3, 512)

    # Bridge
    b1 = conv_block(p4, 1024)

    # Decoder
    d1 = decoder_block(b1, s4, 512)
    d2 = decoder_block(d1, s3, 256)
    d3 = decoder_block(d2, s2, 128)
    d4 = decoder_block(d3, s1, 64)

    # Output
    outputs = tf.keras.layers.Conv2D(1, 1, padding="same", activation="sigmoid")(d4)
    
    if pad_total > 0:
        outputs = tf.keras.layers.Cropping2D(cropping=((pad_top, pad_bottom), (pad_left, pad_right)))(outputs)
        
    model = tf.keras.Model(inputs, outputs, name="U-Net")
    return model
