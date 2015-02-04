
"""
Copyright (C) 2015 Yannik Marchand
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY Yannik Marchand ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL Yannik Marchand BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation 
are those of the authors and should not be interpreted as representing
official policies, either expressed or implied, of Yannik Marchand.
"""

import struct

bytepos = -1
def char():
    global bytepos
    bytepos+=1
    return content[bytepos]

def chars(n):
    s = ''
    for i in range(n):
        s+=char()
    return s

def String():
    s = ''
    c = char()
    while c != '\x00':
        s+=c
        c = char()
    return s

def UI8():
    return ord(char())

def UI16():
    return (UI8()<<8)+UI8()

def UI24():
    return (UI16()<<8)+UI8()

def UI32():
    return (UI16()<<16)+UI16()

## The following HalfToFloat function was made by this guy here:
##   http://forums.devshed.com/python-programming-11/converting-half-precision-floating-hexidecimal-decimal-576842.html
def HalfToFloat(h):
    s = int((h >> 15) & 0x00000001)    # sign
    e = int((h >> 10) & 0x0000001f)    # exponent
    f = int(h & 0x000003ff)            # fraction

    if e == 0:
       if f == 0:
          return int(s << 31)
       else:
          while not (f & 0x00000400):
             f <<= 1
             e -= 1
          e += 1
          f &= ~0x00000400
    elif e == 31:
       if f == 0:
          return int((s << 31) | 0x7f800000)
       else:
          return int((s << 31) | 0x7f800000 | (f << 13))

    e = e + (127 -15)
    f = f << 13

    return int((s << 31) | (e << 23) | f)

def float16(data):
    floats = []
    for i in range(3):
        v = struct.unpack('>H',data[i*2:i*2+2])[0]
        x = HalfToFloat(v)
        str = struct.pack('I',x)
        f = struct.unpack('f',str)[0]
        floats.append(f)
    return floats

def parse(data):
    global content,bytepos
    content = data
    
    mdlstart = content.index('FMDL')
    bytepos = mdlstart-1
    assert chars(4) == 'FMDL'
    chars(12)
    vtxoffs = bytepos+UI32()
    shpoffs = bytepos+UI32()
    chars(8)
    vtxcount = UI16()
    shpcount = UI16()

    bytepos = vtxoffs
    vertices = []
    for i in range(vtxcount):
        assert chars(4) == 'FVTX'
        attrnum = UI8()
        buffnum = UI8()
        UI16()
        vertnum = UI32()
        chars(4)
        attroff = bytepos+UI32()
        chars(4)
        buffoff = bytepos+UI32()
        chars(4)
        vertices.append([attrnum,buffnum,vertnum,attroff,buffoff,i])

    vbuffers = []
    for vertarr in vertices:
        bytepos = vertarr[4]
        buffers = []
        for i in range(vertarr[1]):
            chars(4)
            size = UI32()
            chars(4)
            stride = UI16()
            chars(6)
            dataoff = bytepos+UI32()
            
            bp = bytepos
            bytepos = dataoff
            buffer = chars(size)
            bytepos = bp
            
            elements = []
            for i in range(vertarr[2]):
                elements.append(buffer[stride*i:stride*(i+1)])
            buffers.append(elements)
        vbuffers.append(buffers)

    polygons = []
    for vertarr in vertices:
        bytepos = vertarr[3]
        buffarr = vbuffers[vertarr[5]]
        blarg2 = []
        for i in range(vertarr[0]):
            nameoff = bytepos+UI32()
            buffidx = UI8()
            buffoff = UI24()
            format = UI32()
            
            bp = bytepos
            bytepos = nameoff
            name = String()
            bytepos = bp
            
            blarg3 = []
            if name == '_p0':
                elements = buffarr[buffidx]
                for element in elements:
                    if format == 0x811:
                        blarg3.append(struct.unpack('>fff',element[buffoff:buffoff+12]))
                    elif format == 0x80F:
                        blarg3.append(float16(element[buffoff:buffoff+6]))
                    else:
                        raise ValueError,"Unsupported buffer format "+hex(format)
                blarg2.append(blarg3)
        polygons.append(blarg2)

    bytepos = shpoffs
    length = UI32()
    num = UI32()+1
    assert num == shpcount+1
    shpgroup = []
    for i in range(num):
        chars(12)
        pdata = bytepos+UI32()
        shpgroup.append(pdata)

    indexlists = []
    for i in shpgroup[1:]:
        bytepos = i
        assert chars(4) == 'FSHP'
        nameoffs = bytepos+UI32()
        
        bytepos = nameoffs
        name = String()
        
        bytepos = i+8
        chars(4)
        sectionidx = UI16()
        chars(22)
        bytepos+=UI32()
        chars(12)
        vgcount = UI16()
        chars(2)
        vgoffs = bytepos+UI32()
        idxoffs = bytepos+UI32()
        
        bytepos = idxoffs
        chars(4)
        size = UI32()
        chars(12)
        bytepos += UI32()
        indexbuffer = chars(size)

        indices = []
        for j in range(size/2):
            index = (ord(indexbuffer[j*2])<<8)+ord(indexbuffer[j*2+1])
            indices.append(index)
        indexlists.append(indices)

    model = {
        'Vertices': [],
        'Triangles': []
        }

    for i in range(len(indexlists)):
        polygon = polygons[i][0]
        for vertex in polygon:
            model['Vertices'].append([vertex[0],vertex[1],vertex[2]])

    n = 0
    for i in range(len(indexlists)):
        l = indexlists[i]
        for j in range(len(l)/3):
            model['Triangles'].append([l[j*3]+n,l[j*3+1]+n,l[j*3+2]+n])
        n+=len(polygons[i][0])

    return model
