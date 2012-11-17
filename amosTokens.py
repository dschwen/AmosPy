"""Token table and code to deal with special cases."""
import struct

__author__ = 'stapled'
def readRem(byteStream):
    """The rem - remark/comment type tokens"""
    commentLength = struct.unpack('bb', byteStream.read(2))[1]
    bytesRead = 2
    comment = struct.unpack('%ds' % commentLength, byteStream.read(commentLength))[0].rstrip("\x00")
    bytesRead += commentLength
    return bytesRead, comment

def readVal(byteStream):
    """Values - all seem to be 4 bytes long"""
    intVal = struct.unpack('>i', byteStream.read(4))[0]
    return 4, intVal

def readFloatVal(byteStream):
    """Read a floating point value"""
    floatVal = struct.unpack(">f", byteStream.read(4))[0]
    return 4, floatVal



def readLabelType(byteStream):
    """Labels - for goto, variables, procedure calls etc"""
    bytesRead = 0
    unknown, length, flags = struct.unpack("Hbb", byteStream.read(4))
    bytesRead += 4
    name = struct.unpack("%ds" % length, byteStream.read(length))[0].rstrip("\x00")
    if flags & 1:
        name += "#" #Floats in amos
    elif flags and 2:
        name += "$"
    bytesRead += length
    return bytesRead, name

def unknownSize(size):
    """Some tokens have an 'unknown' extra bytes. Make sure to eat them"""
    def _read(byteStream):
        byteStream.read(size)
        return size, None
    return _read

def readString(byteStream):
    """String constants"""
    bytesRead = 0
    length = struct.unpack(">h", byteStream.read(2))[0]
    bytesRead += 2
    #Round to next word boundary
    if length % 2:
        length += 1
    data = struct.unpack("%ds" % length, byteStream.read(length))[0].rstrip("\x00")
    bytesRead += length
    return bytesRead, data

def readProcedure(byteStream):
    """This is the procedure declaration. So far - nothing can be done for a compiled or encrypted one"""
    bytesRead = 0
    bytesToEnd, encSeed, flagsB, encSeed2 = struct.unpack(">ihbb", byteStream.read(8))
    bytesRead += 8
    flags = set()
    if flagsB & 2 ** 7:
        flags.add('folded')
    if flagsB & 2 ** 6:
        flags.add('locked')
    if flagsB & 2 ** 5:
        flags.add('encrypted')
    if flagsB & 2 ** 4:
        flags.add('compiled')
    if 'compiled' in flags:
        byteStream.read(bytesToEnd)
        bytesRead += bytesToEnd
    return bytesRead, {'bytesToEnd': bytesToEnd, 'encSeed': (encSeed, encSeed2), 'flags': flags}

def readExtension(byteStream):
    """An extension token. For now - look in extensions.py for their mappings"""
    extNo, unused, extToken = struct.unpack('>2bH', byteStream.read(4))
    return 6, (extNo, extToken)

#Given majority have no extra, a simple string, or length 1 tuple is the default
token_map = {
    0x0000: (None,),
    0x0006: ('Variable', readLabelType),
    0x000c: ('Label', readLabelType),
    0x0012: ('Call', readLabelType),
    0x0018: ('Goto Label Ref', readLabelType),
    0x001e: ('BinVal', readVal),
    0x0026: ('Dbl Str', readString),
    0x002e: ('Sgl Str', readString),
    0x0036: ('HexVal', readVal),
    0x003e: ('DecVal', readVal),
    0x0046: ('Float', readFloatVal),
    0x004e: ('Extension', readExtension),
    0x0054: ':',
    0x005c: ',',
    0x0064: ';',
    0x006c: '#',
    0x0074: '(',
    0x007c: ')',
    0x0084: '[',
    0x008c: ']',
    0x0094: 'To',
    0x009c: 'Not',
    0x00a6: 'Swap',
    0x00b0: 'Def Fn',
    0x00bc: 'Fn',
    0x00c4: 'Follow Off',
    0x00d4: 'Follow',
    0x00e0: 'Resume Next',
    0x00f2: 'Inkey$',
    0x00fe: 'Repeat$',
    0x010e: 'Zone$',
    0x011c: 'Border$',
    0x012c: 'Double Buffer',
    0x0140: 'Start',
    0x014c: 'Length',
    0x015a: 'Doke',
    0x0168: 'On Menu Del',
    0x017a: 'On Menu On',
    0x018a: 'On Menu Off',
    0x019c: 'Every On',
    0x01aa: 'Every Off',
    0x01ba: 'Logbase',
    0x01c8: 'Logic',
    0x01d4: 'Logic',
    0x01dc: 'Asc',
    0x01e6: 'As',
    0x01ee: 'Call',
    0x01f8: 'Execall',
    0x0206: 'Gfxcall',
    0x0214: 'Doscall',
    0x0222: 'Intcall',
    0x0230: 'Freeze',
    0x023c: ('For', unknownSize(2)),
    0x0246: 'Next',
    0x0250: ('Repeat', unknownSize(2)),
    0x025c: 'Until',
    0x0268: ('While', unknownSize(2)),
    0x0274: 'Wend',
    0x027e: ('Do', unknownSize(2)),
    0x0286: 'Loop',
    0x0290: ('Exit If', unknownSize(4)),
    0x029e: ('Exit', unknownSize(4)),
    0x02a8: 'Goto',
    0x02b2: 'Gosub',
    0x02be: ('If', unknownSize(2)),
    0x02c6: 'Then',
    0x02d0: ('Else', unknownSize(2)),
    0x02da: 'EndIf',
    0x02e6: 'On Error',
    0x02f4: 'On Break Proc',
    0x0308: 'On Menu',
    0x0316: ('On', unknownSize(4)),
    0x031e: 'Resume Label',
    0x0330: 'Resume',
    0x033c: 'Pop Proc',
    0x034a: 'Every',
    0x0356: 'Step',
    0x0360: 'Return',
    0x036c: 'Pop',
    0x0376: ('Procedure', readProcedure),
    0x0386: 'Proc',
    0x0390: 'End Proc',
    0x039e: 'Shared',
    0x03aa: 'Global',
    0x03b6: 'End',
    0x03c0: 'Stop',
    0x03ca: 'Param#',
    0x03d6: 'Param$',
    0x03e2: 'Param',
    0x03ee: 'Error',
    0x03fa: 'Errn',
    0x0404: ('Data', unknownSize(2)),
    0x040e: 'Read',
    0x0418: 'Restore',
    0x0426: 'Break Off',
    0x0436: 'Break On',
    0x0444: 'Inc',
    0x044e: 'Dec',
    0x0458: 'Add',
    0x0462: 'Add',
    0x046a: 'Print #',
    0x0476: 'Print',
    0x0482: 'Lprint',
    0x048e: 'Input$',
    0x049c: 'Input$',
    0x04a6: 'Using',
    0x04b2: 'Input #',
    0x04be: 'Line Input #',
    0x04d0: 'Input',
    0x04dc: 'Line Input',
    0x04ec: 'Run',
    0x04f6: 'Run',
    0x04fe: 'Set Buffer',
    0x050e: 'Mid$',
    0x051e: 'Mid$',
    0x0528: 'Left$',
    0x0536: 'Right$',
    0x0546: 'Flip$',
    0x0552: 'Chr$',
    0x055e: 'Space$',
    0x056c: 'String$',
    0x057c: 'Upper$',
    0x058a: 'Lower$',
    0x0598: 'Str$',
    0x05a4: 'Val',
    0x05ae: 'Bin$',
    0x05ba: 'Bin$',
    0x05c4: 'Hex$',
    0x05d0: 'Hex$',
    0x05da: 'Len',
    0x05e4: 'Instr$',
    0x05f4: 'Instr$',
    0x0600: 'Tab$',
    0x060a: 'Free',
    0x0614: 'Varptr',
    0x0620: 'Remember X',
    0x0630: 'Remember Y',
    0x0640: 'Dim',
    0x064a: ('Rem', readRem),
    0x0652: ("'", readRem),
    0x0658: 'Sort',
    0x0662: 'Match',
    0x0670: 'Edit',
    0x067a: 'Direct',
    0x0686: 'Rnd',
    0x0690: 'Randomize',
    0x06a0: 'Sgn',
    0x06aa: 'Abs',
    0x06b4: 'Int',
    0x06be: 'Radian',
    0x06ca: 'Degree',
    0x06d6: 'Pi#',
    0x06e0: 'Fix',
    0x06ea: 'Min',
    0x06f6: 'Max',
    0x0702: 'Sin',
    0x070c: 'Cos',
    0x0716: 'Tan',
    0x0720: 'Asin',
    0x072c: 'Acos',
    0x0738: 'Atan',
    0x0744: 'Hsin',
    0x0750: 'Hcos',
    0x075c: 'Htan',
    0x0768: 'Sqrt',
    0x0772: 'Log',
    0x077c: 'Ln',
    0x0786: 'Exp',
    0x0790: 'Menu To Bank',
    0x07a4: 'Bank To Menu',
    0x07b8: 'Menu On',
    0x07c6: 'Menu Off',
    0x07d4: 'Menu Calc',
    0x07e4: 'Menu Mouse On',
    0x07f8: 'Menu Mouse Off',
    0x080c: 'Menu Base',
    0x081e: 'Set Menu',
    0x0832: 'X Menu',
    0x0840: 'Y Menu',
    0x084e: 'Menu Key',
    0x0862: 'Menu Bar',
    0x0872: 'Menu Line',
    0x0882: 'Menu Tline',
    0x0894: 'Menu Movable',
    0x08a8: 'Menu Static',
    0x08ba: 'Menu Item Movable',
    0x08d2: 'Menu Item Static',
    0x08ea: 'Menu Active',
    0x08fc: 'Menu Inactive',
    0x0910: 'Menu Separate',
    0x0924: 'Menu Link',
    0x0934: 'Menu Called',
    0x0946: 'Menu Once',
    0x0956: 'Menu Del',
    0x0964: 'Menu$',
    0x0970: 'Choice',
    0x097e: 'Choice',
    0x0986: 'Screen Copy',
    0x099c: 'Screen Copy',
    0x09a8: 'Screen Copy',
    0x09be: 'Screen Copy',
    0x09d6: 'Screen Clone',
    0x09ea: 'Screen Open',
    0x0a04: 'Screen Close',
    0x0a18: 'Screen Display',
    0x0a36: 'Screen Offset',
    0x0a4e: 'Screen Size',
    0x0a5e: 'Screen Colour',
    0x0a72: 'Screen To Front',
    0x0a88: 'Screen To Front',
    0x0a90: 'Screen To Back',
    0x0aa6: 'Screen To Back',
    0x0aae: 'Screen Hide',
    0x0ac0: 'Screen Hide',
    0x0ac8: 'Screen Show',
    0x0ada: 'Screen Show',
    0x0ae2: 'Screen Swap',
    0x0af4: 'Screen Swap',
    0x0afc: 'Save If',
    0x0b0c: 'Save Iff',
    0x0b16: 'View',
    0x0b20: 'Auto View Off',
    0x0b34: 'Auto View On',
    0x0b46: 'Screen Base',
    0x0b58: 'Screen Width',
    0x0b6c: 'Screen Width',
    0x0b74: 'Screen Height',
    0x0b88: 'Screen Height',
    0x0b90: 'Get Palette',
    0x0ba4: 'Get Palette',
    0x0bae: 'Cls',
    0x0bb8: 'Cls',
    0x0bc0: 'Cls',
    0x0bd0: 'Def Scroll',
    0x0bee: 'X Hard',
    0x0bfc: 'X Hard',
    0x0c06: 'Y Hard',
    0x0c14: 'Y Hard',
    0x0c1e: 'X Screen',
    0x0c2e: 'X Screen',
    0x0c38: 'Y Screen',
    0x0c48: 'Y Screen',
    0x0c52: 'X Text',
    0x0c60: 'Y Text',
    0x0c6e: 'Screen',
    0x0c7c: 'Screen',
    0x0c84: 'Hires',
    0x0c90: 'Lowres',
    0x0c9c: 'Dual Playfield',
    0x0cb4: 'Dual Priority',
    0x0cca: 'Wait Vbl',
    0x0cd8: 'Default Palette',
    0x0cee: 'Default',
    0x0cfc: 'Palette',
    0x0d0a: 'Colour Back',
    0x0d1c: 'Colour',
    0x0d2c: 'Colour',
    0x0d34: 'Flash Off',
    0x0d44: 'Flash',
    0x0d52: 'Shift Off',
    0x0d62: 'Shift Up',
    0x0d78: 'Shift Down',
    0x0d90: 'Set Rainbow',
    0x0dae: 'Set Rainbow',
    0x0dc2: 'Rainbow Del',
    0x0dd4: 'Rainbow Del',
    0x0ddc: 'Rainbow',
    0x0df0: 'Rain',
    0x0dfe: 'Fade',
    0x0e08: 'Phybase',
    0x0e16: 'Physic',
    0x0e24: 'Physic',
    0x0e2c: 'Autoback',
    0x0e3c: 'Plot',
    0x0e4a: 'Plot',
    0x0e56: 'Point',
    0x0e64: 'Draw To',
    0x0e74: 'Draw',
    0x0e86: 'Ellipse',
    0x0e9a: 'Circle',
    0x0eac: 'Polyline to',
    0x0eba: 'Polygon',
    0x0ec8: 'Bar',
    0x0ed8: 'Box',
    0x0ee8: 'Paint',
    0x0ef8: 'Paint',
    0x0f04: 'Gr Locate',
    0x0f16: 'Text Length',
    0x0f28: 'Text Style',
    0x0f38: 'Text Base',
    0x0f3a: 'Text Base',
    0x0f4a: 'Text',
    0x0f5a: 'Set Text',
    0x0f6a: 'Set Paint',
    0x0f7a: 'Get Fonts',
    0x0f8a: 'Get Disc Fonts',
    0x0f9e: 'Get Rom Fonts',
    0x0fb2: 'Set Font',
    0x0fc2: 'Font',
    0x0fce: 'HSlider',
    0x0fe8: 'VSlider',
    0x1002: 'Set Slider',
    0x1022: 'Set Pattern',
    0x1034: 'Set Line',
    0x1044: 'Ink',
    0x1050: 'Ink',
    0x105a: 'Ink',
    0x1066: 'Gr Writing',
    0x1078: 'Clip',
    0x1084: 'Clip',
    0x1092: 'Set Tempras',
    0x10a4: 'Set Tempras',
    0x10ac: 'Set Tempras',
    0x10b6: 'Appear',
    0x10c8: 'Appear',
    0x10d6: 'Zoom',
    0x10f4: 'Get Cblock',
    0x110e: 'Put Cblock',
    0x1120: 'Put Cblock',
    0x112c: 'Del Cblock',
    0x113e: 'Del Cblock',
    0x1146: 'Get Block',
    0x1160: 'Get Block',
    0x1172: 'Put Block',
    0x1184: 'Put Block',
    0x1190: 'Put Block',
    0x119e: 'Put Block',
    0x11ae: 'Del Block',
    0x11be: 'Del Block',
    0x11c6: 'Key Speed',
    0x11d8: 'Key State',
    0x11e8: 'Key Shift',
    0x11f8: 'Joy',
    0x1202: 'Jup',
    0x120c: 'Jdown',
    0x1218: 'Jleft',
    0x1224: 'Jright',
    0x1232: 'Fire',
    0x123e: 'True',
    0x1248: 'False',
    0x1254: 'Put Key',
    0x1262: 'Scancode',
    0x1270: 'Scanshift',
    0x1280: 'Clear Key',
    0x1290: 'Wait Key',
    0x129e: 'Wait',
    0x12aa: 'Key$',
    0x12b6: 'Scan$',
    0x12bc: 'Scan$',
    0x12c4: 'Scan$',
    0x12ce: 'Timer',
    0x12da: 'Wind Open',
    0x12f4: 'Wind Open',
    0x1306: 'Wind Open',
    0x131a: 'Wind Close',
    0x132a: 'Wind Save',
    0x133a: 'Wind Move',
    0x134c: 'Wind Size',
    0x135e: 'Window',
    0x136c: 'Windon',
    0x1378: 'Locate',
    0x1388: 'Clw',
    0x1392: 'Home',
    0x139c: 'Curs Pen',
    0x13ac: 'Pen$',
    0x13b8: 'Paper$',
    0x13c6: 'At',
    0x13d2: 'Pen',
    0x13dc: 'Paper',
    0x13e8: 'Center',
    0x13f6: 'Border',
    0x1408: 'Writing',
    0x1418: 'Writing',
    0x1422: 'Title Top',
    0x1432: 'Title Bottom',
    0x1446: 'Curs Off',
    0x1454: 'Curs On',
    0x1462: 'Inverse Off',
    0x1474: 'Inverse On',
    0x1484: 'Under Off',
    0x1494: 'Under On',
    0x14a2: 'Shade Off',
    0x14b2: 'Shade On',
    0x14c0: 'Scroll Off',
    0x14d0: 'Scroll On',
    0x14e0: 'Scroll',
    0x14ee: 'Cup$',
    0x14f8: 'CDown$',
    0x1504: 'CLeft$',
    0x1510: 'CRight$',
    0x151e: 'Cup',
    0x1528: 'Cdown',
    0x1534: 'Cleft',
    0x1540: 'Cright',
    0x154c: 'Memorize X',
    0x155c: 'Memorize Y',
    0x156c: 'Cmove$',
    0x157c: 'CMove',
    0x158a: 'Cline',
    0x1596: 'Cline',
    0x159e: 'Hscroll',
    0x15ac: 'Vscroll',
    0x15ba: 'Set Tab',
    0x15c8: 'Set Curs',
    0x15e6: 'X Curs',
    0x15f2: 'Y Curs',
    0x15fe: 'X Graphics',
    0x160e: 'Y Graphics',
    0x161e: 'Xgr',
    0x1628: 'Ygr',
    0x1632: 'Reserve Zone',
    0x1646: 'Reserve Zone',
    0x164e: 'Reset Zone',
    0x1660: 'Reset Zone',
    0x1668: 'Set Zone',
    0x1680: 'Zone',
    0x168e: 'Zone',
    0x169a: 'HZone',
    0x16aa: 'Hzone',
    0x16b6: 'Scin',
    0x16c4: 'Scin',
    0x16d0: 'Mouse Screen',
    0x16e2: 'Mouse Zone',
    0x16f2: 'Set Input',
    0x1704: 'Close Workbench',
    0x171a: 'Close Editor',
    0x172c: 'Dir First',
    0x173e: 'Dir Next',
    0x174e: 'Exist',
    0x175a: 'Dir$',
    0x1766: 'Ldir/w',
    0x1774: 'Ldir/w',
    0x177c: 'Dir/w',
    0x1788: 'Dir/w',
    0x1790: 'Ldir',
    0x179c: 'Ldir',
    0x17a4: 'Dir',
    0x17ae: 'Dir',
    0x17b6: 'Set Dir',
    0x17c4: 'Set Dir',
    0x17d4: 'Load Iff',
    0x17e4: 'Load Iff',
    0x17ee: 'Mask Iff',
    0x17fe: 'Picture',
    0x180c: 'Bload',
    0x181a: 'Bsave',
    0x1820: 'Pload',
    0x182a: 'Pload',
    0x1838: 'Save',
    0x1844: 'Save',
    0x184e: 'Load',
    0x185a: 'Load',
    0x1864: 'Dfree',
    0x1870: 'Mkdir',
    0x187c: 'Lof',
    0x1886: 'Eof',
    0x1890: 'Pof',
    0x189c: 'Port',
    0x18a8: 'Open Random',
    0x18bc: 'Open In',
    0x18cc: 'Open Out',
    0x18de: 'Open Port',
    0x18f0: 'Append',
    0x1900: 'Close',
    0x190c: 'Close',
    0x1914: 'Parent',
    0x1920: 'Rename',
    0x1930: 'Kill',
    0x193c: 'Drive',
    0x1948: 'Field',
    0x1954: 'Fsel$',
    0x1962: 'Fsel$',
    0x196c: 'Fsel$',
    0x1978: 'Fsel$',
    0x1986: 'Set Sprite Buffer',
    0x199e: 'Sprite Off',
    0x19b0: 'Sprite Off',
    0x19b8: 'Sprite Priority',
    0x19ce: 'Sprite Update Off',
    0x19e6: 'Sprite Update On',
    0x19fc: 'Sprite Update',
    0x1a10: 'Spritebob Col',
    0x1a26: 'Spritebob Col',
    0x1a32: 'Sprite Col',
    0x1a44: 'Sprite Col',
    0x1a50: 'Set Hardcol',
    0x1a64: 'Hardcol',
    0x1a72: 'Sprite Base',
    0x1a84: 'Icon Base',
    0x1a94: 'Sprite',
    0x1aa8: 'Bob Off',
    0x1ab6: 'Bob Off',
    0x1abe: 'Bob Update Off',
    0x1ad2: 'Bob Update On',
    0x1ae6: 'Bob Update',
    0x1af6: 'Bob Clear',
    0x1b06: 'Bob Draw',
    0x1b14: 'Bobsprite Col',
    0x1b2a: 'Bobsprite Col',
    0x1b36: 'Bob Col',
    0x1b46: 'Bob Col',
    0x1b52: 'Col',
    0x1b5c: 'Limit Bob',
    0x1b64: 'Limit Bob',
    0x1b6c: 'Limit Bob',
    0x1b7a: 'Limit Bob',
    0x1b8a: 'Set Bob',
    0x1b9e: 'Bob',
    0x1bae: 'Get Sprite Palette',
    0x1bc8: 'Get Sprite Palette',
    0x1bd0: 'Get Sprite',
    0x1bea: 'Get Sprite',
    0x1bfc: 'Get Bob',
    0x1c14: 'Get Bob',
    0x1c26: 'Del Sprite',
    0x1c38: 'Del Sprite',
    0x1c42: 'Del Bob',
    0x1c52: 'Del Bob',
    0x1c5c: 'Del Icon',
    0x1c6c: 'Del Icon',
    0x1c76: 'Ins Sprite',
    0x1c88: 'Ins Bob',
    0x1c96: 'Ins Icon',
    0x1ca6: 'Get Icon Palette',
    0x1cbe: 'Get Icon Palette',
    0x1cc6: 'Get Icon',
    0x1cde: 'Get Icon',
    0x1cf0: 'Put Bob',
    0x1cfe: 'Paste Bob',
    0x1d12: 'Paste Icon',
    0x1d28: 'Make Mask',
    0x1d38: 'Make Mask',
    0x1d40: 'No Mask',
    0x1d4e: 'No Mask',
    0x1d56: 'Make Icon Mask',
    0x1d6c: 'Make Icon Mask',
    0x1d74: 'No Icon Mask',
    0x1d88: 'No Icon Mask',
    0x1d90: 'Hot Spot',
    0x1da2: 'Hot Spot',
    0x1dae: 'Priority On',
    0x1dc0: 'Priority Off',
    0x1dd2: 'Hide On',
    0x1de0: 'Hide',
    0x1dea: 'Show On',
    0x1df8: 'Show',
    0x1e02: 'Change Mouse',
    0x1e16: 'X Mouse',
    0x1e24: 'Y Mouse',
    0x1e32: 'Mouse Key',
    0x1e42: 'Mouse Click',
    0x1e54: 'Limit Mouse',
    0x1e66: 'Limit Mouse',
    0x1e6e: 'Limit Mouse',
    0x1e7c: 'Unfreeze',
    0x1e8a: 'Move X',
    0x1e9a: 'Move X',
    0x1ea6: 'Move Y',
    0x1eb6: 'Move y',
    0x1ec2: 'Move Off',
    0x1ed2: 'Move Off',
    0x1eda: 'Move On',
    0x1ee8: 'Move On',
    0x1ef0: 'Move Freeze',
    0x1f02: 'Move Freeze',
    0x1f0a: 'Anim Off',
    0x1f1a: 'Anim Off',
    0x1f22: 'Anim On',
    0x1f30: 'Anim On',
    0x1f38: 'Anim Freeze',
    0x1f4a: 'Anim Freeze',
    0x1f52: 'Anim',
    0x1f60: 'Anim',
    0x1f6c: 'Movon',
    0x1f78: 'Chanan',
    0x1f86: 'Chanmv',
    0x1f94: 'Channel',
    0x1fa2: 'Amreg',
    0x1fb0: 'Amreg',
    0x1fbc: 'Amal On',
    0x1fca: 'Amal On',
    0x1fd2: 'Amal Off',
    0x1fe2: 'Amal Off',
    0x1fea: 'Amal Freeze',
    0x1ffc: 'Amal Freeze',
    0x2004: 'Amalerr',
    0x2012: 'Amal',
    0x2020: 'Amal',
    0x202c: 'Amplay',
    0x203c: 'Amplay',
    0x204a: 'Synchro On',
    0x205a: 'Synchro Off',
    0x206c: 'Synchro',
    0x207a: 'Update Off',
    0x208a: 'Update On',
    0x209a: 'Update Every',
    0x20ae: 'Update',
    0x20ba: 'X Bob',
    0x20c6: 'Y Bob',
    0x20d2: 'X Sprite',
    0x20e2: 'Y Sprite',
    0x20f2: 'Reserve As Work',
    0x210a: 'Reserve As Chip Work',
    0x2128: 'Reserve As Data',
    0x2140: 'Reserve As Chip Data',
    0x215e: 'Erase',
    0x216a: 'List Bank',
    0x217a: 'Chip Free',
    0x218a: 'Fast Free',
    0x219a: 'Fill',
    0x21aa: 'Copy',
    0x21ba: 'Hunt',
    0x21ca: 'Poke',
    0x21d8: 'Loke',
    0x21e6: 'Peek',
    0x21f2: 'Deek',
    0x21fe: 'Leek',
    0x220a: 'Bset.<>',
    0x2218: 'Bclr',
    0x2226: 'Bchg',
    0x2234: 'Btst',
    0x2242: 'Ror.<>',
    0x2250: 'Ror.w',
    0x225e: 'Ror.l',
    0x226c: 'Rol.<>',
    0x227a: 'Rol.w',
    0x2288: 'Rol.l',
    0x2296: 'Areg',
    0x22a2: 'Dreg',
    0x22ae: 'Copper On',
    0x22be: 'Copper Off',
    0x22ce: 'Cop Swap',
    0x22dc: 'Cop Reset',
    0x22ec: 'Cop Wait',
    0x22fe: 'Cop Wait',
    0x230c: 'Cop Movel',
    0x231e: 'Cop Move',
    0x2330: 'Cop Logic',
    0x2340: 'Prg First$',
    0x2352: 'Prg Next$',
    0x2362: 'Psel$',
    0x2370: 'Psel$',
    0x237a: 'Psel$',
    0x2386: 'Psel$',
    0x2394: 'Prun',
    0x23a0: 'Bgrab',
    0x23ac: 'Put',
    0x23b8: 'Get',
    0x23c4: 'System',
    0x23d0: 'Multi Wait',
    0x23e0: 'I Bob',
    0x23ec: 'I Sprite',
    0x23fc: 'Priority Reverse On',
    0x2416: 'Priority Reverse Off',
    0x2430: 'Dev First',
    0x2442: 'Dev Next',
    0x2452: 'Hrev Block',
    0x2464: 'Vrev Block',
    0x2476: 'Hrev',
    0x2482: 'Vrev',
    0x248e: 'Rev',
    0x2498: 'Bank Swap',
    0x24aa: 'Amos To Front',
    0x24be: 'Amos To Back',
    0x24d0: 'Amos Here',
    0x24e0: 'Amos Lock',
    0x24f0: 'Amos Unlock',
    0x2502: 'Display Height',
    0x2516: 'Ntsc',
    0x2520: 'Laced',
    0x252c: 'Prg State',
    0x253c: 'Command Line$',
    0x2550: 'Disc Info$',
    0x292a: 'Read Text',
    0xff3e: 'Xor',
    0xff4c: 'Or',
    0xff58: 'And',
    0xff66: '<>',
    0xff70: '><',
    0xff7a: '<=',
    0xff84: '=<',
    0xff8e: '>=',
    0xff98: '=>',
    0xffa2: '=',
    0xffac: '<',
    0xffb6: '>',
    0xffc0: '+',
    0xffca: '-',
    0xffd4: 'Mod',
    0xffe2: '*',
    0xffec: '/',
    0xfff6: '^',
    }

