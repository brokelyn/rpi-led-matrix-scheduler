#sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
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
    options.pwm_bits = 11
    options.brightness = 75
    options.pwm_lsb_nanoseconds = 120
    options.led_rgb_sequence = 'RGB'
    options.pixel_mapper_config = ''
    options.panel_type = ''
    #options.show_refresh_rate = 1
    options.gpio_slowdown = 5
    options.disable_hardware_pulsing = False
    options.drop_privileges = False

    return RGBMatrix(options=options)
