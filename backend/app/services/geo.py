from typing import Any
ALLOWED={'Point','LineString','Polygon'}
def validate_geometry(g:dict[str,Any]|None):
    if g is None:return
    if g.get('type') not in ALLOWED: raise ValueError('Geometry must be Point, LineString, or Polygon')
    c=g.get('coordinates')
    if g['type']=='Point' and (not isinstance(c,list) or len(c)!=2): raise ValueError('Invalid Point geometry')
    if g['type']=='LineString' and (not isinstance(c,list) or len(c)<2): raise ValueError('LineString requires at least two coordinates')
    if g['type']=='Polygon' and (not isinstance(c,list) or not c or len(c[0])<4): raise ValueError('Polygon requires a closed ring')
    def check(pt):
        if not isinstance(pt,list) or len(pt)!=2 or not all(isinstance(x,(int,float)) for x in pt) or not(-180<=pt[0]<=180 and -90<=pt[1]<=90): raise ValueError('Invalid coordinate')
    if g['type']=='Point': check(c); return
    pts=c if g['type']=='LineString' else c[0]
    for pt in pts: check(pt)
    if g['type']=='Polygon' and pts[0]!=pts[-1]: raise ValueError('Polygon ring must be closed')
