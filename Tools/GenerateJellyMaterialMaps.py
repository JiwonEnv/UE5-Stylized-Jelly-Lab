"""Generate repeatable prototype material maps for the JellyGame test mesh."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1] / 'SourceAssets' / 'MaterialPrototypes'
N = 2048

def field(seed, scale):
    rng = np.random.default_rng(seed)
    a = rng.integers(0,256,(scale,scale),dtype=np.uint8)
    return np.asarray(Image.fromarray(a).resize((N,N), Image.Resampling.BICUBIC),dtype=np.float32)/255

def save(name, kind, a):
    folder=ROOT/name; folder.mkdir(parents=True,exist_ok=True)
    Image.fromarray(np.uint8(np.clip(a,0,1)*255)).save(folder/(name+'_'+kind+'.png'))

def output(name, height, mask, color, rough, normal_strength):
    h=np.clip(height,0,1); m=np.clip(mask,0,1)
    gx=(np.roll(h,-1,axis=1)-np.roll(h,1,axis=1))*normal_strength
    gy=(np.roll(h,-1,axis=0)-np.roll(h,1,axis=0))*normal_strength
    normal=np.stack((-gx,gy,np.ones_like(h)),axis=-1)
    normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    ao=np.clip(1-(1-h)*0.26,0,1); metallic=np.zeros_like(h)
    save(name,'BaseColor',color); save(name,'Normal_DirectX',normal*.5+.5)
    save(name,'Roughness',rough); save(name,'Mask',m); save(name,'Height',h)
    save(name,'ORM',np.stack((ao,rough,metallic),axis=-1))

rng=np.random.default_rng(1834)
canvas=Image.new('L',(N,N),0); draw=ImageDraw.Draw(canvas)
for i in range(2800):
    x,y=rng.integers(0,N,2); rx=int(rng.integers(2,15)); ry=int(rx*rng.uniform(.5,1.3)); v=int(rng.integers(100,245))
    for dx in (-N,0,N):
        for dy in (-N,0,N): draw.ellipse((x+dx-rx,y+dy-ry,x+dx+rx,y+dy+ry),fill=v)
pores=np.asarray(canvas.filter(ImageFilter.GaussianBlur(1.3)),dtype=np.float32)/255
grain=field(12,420); mottled=field(14,31); h=np.clip(.7-.49*pores+.10*(grain-.5),0,1)
v=np.clip(.55+.24*mottled-.23*pores+.08*(grain-.5),0,1)
color=np.stack((v*1.0,v*.65,v*.34),axis=-1); rough=np.clip(.72+.18*pores+.1*(grain-.5),0,1)
output('Cookie',h,pores,color,rough,3.0)

canvas=Image.new('L',(N,N),0); draw=ImageDraw.Draw(canvas)
for i in range(26000):
    x,y=rng.integers(0,N,2); angle=rng.uniform(-.65,.65); length=rng.uniform(5,48); dx=int(np.cos(angle)*length); dy=int(np.sin(angle)*length)
    val=int(rng.integers(50,190)); width=int(rng.integers(1,3))
    for ox in (-N,0,N):
        for oy in (-N,0,N): draw.line((x+ox,y+oy,x+dx+ox,y+dy+oy),fill=val,width=width)
fib=np.asarray(canvas.filter(ImageFilter.GaussianBlur(.6)),dtype=np.float32)/255
cloud=field(22,75); h=np.clip(.55+fib*.23+(cloud-.5)*.05,0,1)
v=np.clip(.88+(cloud-.5)*.08-fib*.10,0,1)
color=np.stack((v,v*.987,v*.955),axis=-1); rough=np.clip(.87+fib*.08+(cloud-.5)*.05,0,1)
output('Tissue',h,fib,color,rough,2.0)

canvas=Image.new('L',(N,N),0); draw=ImageDraw.Draw(canvas)
for i in range(12500):
    x,y=rng.integers(0,N,2); angle=rng.uniform(0,2*np.pi); length=rng.uniform(8,90); dx=int(np.cos(angle)*length); dy=int(np.sin(angle)*length)
    val=int(rng.integers(70,240)); width=int(rng.integers(1,4))
    for ox in (-N,0,N):
        for oy in (-N,0,N): draw.line((x+ox,y+oy,x+dx+ox,y+dy+oy),fill=val,width=width)
fiber=np.asarray(canvas.filter(ImageFilter.GaussianBlur(.7)),dtype=np.float32)/255
patch=field(31,40); fleck=field(32,240); mask=np.clip((patch-.38)*2+fiber*.55,0,1)
h=np.clip(.5+fiber*.3+(fleck-.5)*.08,0,1); v=np.clip(.30+patch*.18+fiber*.12+(fleck-.5)*.05,0,1)
color=np.stack((v,v*.96,v*.91),axis=-1); rough=np.clip(.80+mask*.16,0,1)
output('Dust',h,mask,color,rough,2.5)
print('Generated prototypes:', ROOT)
