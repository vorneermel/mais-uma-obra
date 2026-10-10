from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent
imgs=sorted((R/'tmp').glob('pagina-*.png'))
assert len(imgs)==66,len(imgs)
for start in range(0,66,24):
    sheet=Image.new('RGB',(1200,1980),'#ddd');d=ImageDraw.Draw(sheet)
    for j,p in enumerate(imgs[start:start+24]):
        im=Image.open(p).convert('RGB');im.thumbnail((280,300))
        x=(j%4)*300+(300-im.width)//2;y=(j//4)*330
        sheet.paste(im,(x,y+20));d.text(((j%4)*300+10,y+3),str(start+j+1),fill='black')
    sheet.save(R/'tmp'/f'contato-{start//24+1}.jpg')
print('66 páginas renderizadas; 3 folhas de contato')
