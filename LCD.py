"""
MicroPython Character LCD Display library for ESP8266.

Uses 4-bit mode.
Requires 6 GPIO pins.
"""

from time import sleep
import machine


class CharLCD(object):
    """Character LCD Display."""

    LCD_CHR = 1  # Character mode
    LCD_CMD = 0  # Command mode

    # LCD RAM address for display lines
    LCD_LINES = (0x80,  0xC0,  0x94,  0xD4)
    LCD_ROW_OFFSETS = (0x00, 0x40, 0x14, 0x54)

    # Command constants
    LCD_CLEAR = 0x01
    LCD_CURSORSHIFT = 0x10
    LCD_DISPLAYCONTROL = 0x08
    LCD_HOME = 0x02
    LCD_SETDDRAMADDR = 0x80
    LCD_SETCGRAMADDR = 0x40

    # Control flags
    LCD_DISPLAYON = 0x04
    LCD_DISPLAYOFF = 0x00
    LCD_CURSORON = 0x02
    LCD_CURSOROFF = 0x00
    LCD_BLINKON = 0x01
    LCD_BLINKOFF = 0x00

    # Move flags
    LCD_DISPLAYMOVE = 0x08
    LCD_MOVELEFT = 0x00
    LCD_MOVERIGHT = 0x04

    # Timing constants
    E_PULSE = 0.0005
    E_DELAY = 0.0005
    HOMEDELAY = 0.05

    def __init__(self, rs=1, en=3, d4=15, d5=13, d6=12, d7=14,
                 cols=16, rows=2):
        """Constructor for LCD.

        Args:
            rs (int):  Register select address GPIO pin.
            en (int):  Enable GPIO pin.
            d4 (int): Data4 GPIO pin.
            d5 (int): Data5 GPIO pin.
            d6 (int): Data6 GPIO pin.
            d7 (int): Data7 GPIO pin.
            cols (int): Number of character columns.
            lines (int): Number of display rows.
        """
        # Define GPIO to LCD mapping
        self.rs = machine.Pin(rs, machine.Pin.OUT)
        self.en = machine.Pin(en, machine.Pin.OUT)
        self.d4 = machine.Pin(d4, machine.Pin.OUT)
        self.d5 = machine.Pin(d5, machine.Pin.OUT)
        self.d6 = machine.Pin(d6, machine.Pin.OUT)
        self.d7 = machine.Pin(d7, machine.Pin.OUT)
        self.cols = cols
        self.rows = rows

        # Initialise display
        self.lcd_byte(0x33, self.LCD_CMD)
        self.lcd_byte(0x32, self.LCD_CMD)
        self.lcd_byte(0x28, self.LCD_CMD)
        self.lcd_byte(0x0C, self.LCD_CMD)
        self.lcd_byte(0x06, self.LCD_CMD)
        self.clear()

        self.displaycontrol = (
            self.LCD_DISPLAYON | self.LCD_CURSOROFF | self.LCD_BLINKOFF)

    def clear(self):
        """Clear and home LCD display."""
        self.lcd_byte(self.LCD_CLEAR, self.LCD_CMD)
        sleep(self.HOMEDELAY)  # required

    def create_char(self, location, pattern):
        r"""Add custom character to LCD display.

        Args:
            location (int):  There are 8 CGRAM locations available (0 to 7).
            pattern ([byte]):  Byte array comprising custom character.
        Notes:
            There is an online tool to create custom characters:
            http://www.quinapalus.com/hd44780udg.html
            Character size should be 5x8.
            To show your custom character use hex address 0 to 7.
            example:  lcd.message('\x03')
        """
        # only position 0..7 are allowed
        location &= 0x7
        self.lcd_byte(self.LCD_SETCGRAMADDR | (location << 3), self.LCD_CMD)
        for i in range(8):
            self.lcd_byte(pattern[i], self.LCD_CHR)

    def enable(self, enable=True):
        """Enable or disable display.

        Args:
            enable (bool):  True = On (default), False = Off
        """
        if enable:
            self.displaycontrol |= self.LCD_DISPLAYON
        else:
            self.displaycontrol &= ~self.LCD_DISPLAYON

        self.lcd_byte(
            self.LCD_DISPLAYCONTROL | self.displaycontrol, self.LCD_CMD)

    def home(self):
        """Return cursor to home position."""
        self.lcd_byte(self.LCD_HOME, self.LCD_CMD)
        sleep(self.HOMEDELAY)

    def lcd_byte(self, bits, mode):
        """Send command or characters to LCD Display.

        Args:
            bits (byte):  Data to transmit to LCD Display.
            mode (LCD_CHR or LCD_CMD):  Specify character or command mode.
        """
        self.rs.value(mode)
        sleep(self.E_DELAY)

        # High bits
        self.d4.value(0)
        self.d5.value(0)
        self.d6.value(0)
        self.d7.value(0)
        if bits & 0x10 == 0x10:
            self.d4.value(1)
        if bits & 0x20 == 0x20:
            self.d5.value(1)
        if bits & 0x40 == 0x40:
            self.d6.value(1)
        if bits & 0x80 == 0x80:
            self.d7.value(1)

        # Toggle Enable pin.
        sleep(self.E_DELAY)
        self.en.value(1)
        sleep(self.E_PULSE)
        self.en.value(0)
        sleep(self.E_DELAY)

        # Low bits
        self.d4.value(0)
        self.d5.value(0)
        self.d6.value(0)
        self.d7.value(0)
        if bits & 0x01 == 0x01:
            self.d4.value(1)
        if bits & 0x02 == 0x02:
            self.d5.value(1)
        if bits & 0x04 == 0x04:
            self.d6.value(1)
        if bits & 0x08 == 0x08:
            self.d7.value(1)

        # Toggle Enable pin.
        sleep(self.E_DELAY)
        self.en.value(1)
        sleep(self.E_PULSE)
        self.en.value(0)
        sleep(self.E_DELAY)

    def message(self, message, align=0):
        """Display text on LCD display.

        Args:
            message (string):  Text to display.
            align: Justify text.  1-3 fills surrounding area with whitespace.
                0 = No justification
                1 = Left
                2 = Centered
                3 = Right
        Note:
            You should use set_line(), clear(), home() or set_cursor(0, row)
            prior to specifying justified text to ensure the cursor is at the
            beginning of a line.  Otherwise alignment will be incorrect.
        """
        if align == 1:
            message = '{0:<{1}}'.format(message, self.cols)
        elif align == 2:
            message = '{0:^{1}}'.format(message, self.cols)
        elif align == 3:
            message = '{0:>{1}}'.format(message, self.cols)

        for i in range(len(message)):
            self.lcd_byte(ord(message[i]), self.LCD_CHR)

    def move_left(self):
        """Move display left one position."""
        self.lcd_byte(
            self.LCD_CURSORSHIFT | self.LCD_DISPLAYMOVE | self.LCD_MOVELEFT,
            self.LCD_CMD)

    def move_right(self):
        """Move display right one position."""
        self.lcd_byte(
            self.LCD_CURSORSHIFT | self.LCD_DISPLAYMOVE | self.LCD_MOVERIGHT,
            self.LCD_CMD)

    def set_cursor(self, col, row):
        """Move the cursor to an explicit column and row position.

        Args:
            col (int):  Cursor column (zero is first column).
            row (int):  Cursor row (zero is first line).
        """
        # Clamp row to the last row of the display.
        if row > self.rows:
            row = self.rows - 1
        # Set location.
        self.lcd_byte(self.LCD_SETDDRAMADDR | (
            col + self.LCD_ROW_OFFSETS[row]), self.LCD_CMD)

    def set_line(self, num):
        """Set cursor to specified line at column zero.

        Args:
            num (int):  Line number (zero based 0 - 3)
        """
        self.lcd_byte(self.LCD_LINES[num], self.LCD_CMD)

    def show_blink(self, show=True):
        """Enable or disable blinking cursor.

        Args:
            show (bool):  True = On (default), False = Off
        """
        if show:
            self.displaycontrol |= self.LCD_BLINKON
        else:
            self.displaycontrol &= ~self.LCD_BLINKON

        self.lcd_byte(
            self.LCD_DISPLAYCONTROL | self.displaycontrol, self.LCD_CMD)

    def show_underline(self, show=True):
        """Enable or disable underline cursor.

        Args:
            blink (bool):  True = On (default), False = Off
        """
        if show:
            self.displaycontrol |= self.LCD_CURSORON
        else:
            self.displaycontrol &= ~self.LCD_CURSORON

        self.lcd_byte(
            self.LCD_DISPLAYCONTROL | self.displaycontrol, self.LCD_CMD)
