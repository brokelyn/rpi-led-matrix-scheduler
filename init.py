import os
import sys
import settings

sys.path.append(os.path.abspath(settings.PATH_PYTHON_BINDING))

from rgbmatrix import RGBMatrix, RGBMatrixOptions


def init_leds():
    options = RGBMatrixOptions()

    options.hardware_mapping = 'regular'
    options.rows = 32
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.row_address_type = 0
    options.multiplexing = 0
    options.brightness = 85
    options.pwm_bits = 8
    options.pwm_lsb_nanoseconds = 130
    options.led_rgb_sequence = 'RGB'
    options.pixel_mapper_config = ''
    options.panel_type = ''
    options.limit_refresh_rate_hz = 59  # reduce flickering due to high energy consumption
    options.show_refresh_rate = 0
    options.gpio_slowdown = 4
    options.disable_hardware_pulsing = False
    options.drop_privileges = False

    return RGBMatrix(options=options)
