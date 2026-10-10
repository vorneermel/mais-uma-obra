from pathlib import Path
import re,html,json,zipfile,uuid,posixpath
from xml.etree import ElementTree as ET
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from pypdf import PdfReader,PdfWriter
from PIL import Image,ImageDraw,ImageFont

R=Path(__file__).resolve().parent
T=R/'tmp';T.mkdir(exist_ok=True)
TITLE='Mais uma obra';SUB='Os dezessete de Campo Bom'
W,H=420,630
esc=lambda s:html.escape(s,quote=False)
raw=(R/'manuscrito.md').read_text(encoding='utf-8')
chap=[]
for i,p in enumerate(re.split(r'^## ',raw,flags=re.M)[1:],1):
    h,b=p.split('\n',1);ps=[x.strip() for x in b.strip().split('\n\n') if x.strip()]
    chap.append((h,ps));(R/'capitulos'/f'{i:02d}.md').write_text('# '+h+'\n\n'+'\n\n'.join(ps)+'\n',encoding='utf-8')
assert len(chap)==16
back=(R/'contracapa.md').read_text(encoding='utf-8').strip().split('\n\n')[1:]
for n,f in [('G','georgia.ttf'),('GB','georgiab.ttf'),('GI','georgiai.ttf')]:pdfmetrics.registerFont(TTFont(n,'C:/Windows/Fonts/'+f))
pdfmetrics.registerFontFamily('G',normal='G',bold='GB',italic='GI',boldItalic='GB')
class Doc(SimpleDocTemplate):
    def afterFlowable(self,f):
        if hasattr(f,'key'):self.starts[f.key]=self.page
def foot(c,d):
    c.setFont('G',8);c.setFillColor(HexColor('#71685c'));c.drawCentredString(W/2,23,str(d.page+3))
def body(size,counts=None):
    st=ParagraphStyle('body',fontName='G',fontSize=size,leading=size*1.43,firstLineIndent=14,spaceAfter=4,alignment=4,allowWidows=0,allowOrphans=0)
    dia=ParagraphStyle('dia',parent=st,firstLineIndent=0,alignment=0)
    heading=ParagraphStyle('heading',fontName='GB',fontSize=23,leading=29,spaceAfter=24,textColor=HexColor('#215768'))
    story=[]
    for i,(h,ps) in enumerate(chap,1):
        label,name=h.split(' — ',1)
        story.append(Spacer(1,12));story.append(Paragraph('CAPÍTULO '+label,ParagraphStyle('lab',fontName='G',fontSize=9,leading=13,spaceAfter=15)))
        q=Paragraph(esc(name),heading);q.key=i;story.append(q)
        pars=[Paragraph(esc(p),dia if p.startswith('—') or j==0 or p=='FIM' else st) for j,p in enumerate(ps)]
        if counts:
            k=counts[i-1];heights=[p.wrap(W-98,1000)[1]+4 for p in pars]
            overhead=12+28+q.wrap(W-98,1000)[1]+24
            sums=[0]
            for z in heights:sums.append(sums[-1]+z)
            ideal=(sums[-1]+overhead)/k
            dp={(0,0):(0,[])}
            for page in range(1,k+1):
                for end in range(page,len(pars)+1):
                    choices=[]
                    for begin in range(page-1,end):
                        prev=dp.get((page-1,begin))
                        if prev is None:continue
                        used=sums[end]-sums[begin]+(overhead if page==1 else 0)
                        if used<=530:choices.append((prev[0]+(used-ideal)**2,prev[1]+[(begin,end)]))
                    if choices:dp[(page,end)]=min(choices,key=lambda x:x[0])
            assert (k,len(pars)) in dp, f'Falha de balanceamento: capítulo {i}'
            for j,(a,b) in enumerate(dp[(k,len(pars))][1]):
                story.extend(pars[a:b])
                if j<k-1:story.append(PageBreak())
        else:story.extend(pars)
        if i<len(chap):story.append(PageBreak())
    d=Doc(str(T/'body.pdf'),pagesize=(W,H),leftMargin=43,rightMargin=43,topMargin=40,bottomMargin=42);d.starts={}
    d.build(story,onFirstPage=foot,onLaterPages=foot)
    return len(PdfReader(T/'body.pdf').pages),d.starts
# 62 páginas de narrativa, mais capa, rosto, sumário e contracapa = 66.
lo,hi=10.0,15.5;found=None
for _ in range(20):
    size=(lo+hi)/2;n,starts=body(size)
    if n==62:found=(size,starts);break
    if n<62:lo=size
    else:hi=size
assert found, 'Não foi encontrada diagramação natural de 62 páginas'
size,starts=found
counts=[(starts.get(i+1,63)-starts[i]) for i in range(1,17)]
size-=0.5
n,starts=body(size,counts);assert n==62

c=canvas.Canvas(str(T/'front.pdf'),pagesize=(W,H));c.setTitle(TITLE)
c.drawImage(str(R/'arte-capa.png'),0,0,width=W,height=H)
c.setFillColor(HexColor('#123b4f'));c.setFont('GB',36);c.drawCentredString(W/2,H-65,TITLE)
c.setFont('G',14);c.drawCentredString(W/2,H-94,SUB)
c.setFont('G',9);c.drawCentredString(W/2,H-115,'UMA NOVELINHA DE TRABALHO E AMIZADE')
c.showPage();c.save()
im=Image.open(R/'arte-capa.png').convert('RGB');dr=ImageDraw.Draw(im)
for txt,y,sz,font in [(TITLE,120,88,'georgiab.ttf'),(SUB,207,36,'georgia.ttf'),('UMA NOVELINHA DE TRABALHO E AMIZADE',265,23,'georgia.ttf')]:
    f=ImageFont.truetype('C:/Windows/Fonts/'+font,sz);dr.text((im.width/2,y),txt,font=f,fill='#123b4f',anchor='mt')
im.save(R/'capa.png')
c=canvas.Canvas(str(T/'pre.pdf'),pagesize=(W,H));c.setFillColor(HexColor('#123b4f'))
c.setFont('GB',32);c.drawCentredString(W/2,H-170,TITLE);c.setFont('G',16);c.drawCentredString(W/2,H-203,SUB)
c.setFont('G',11);c.drawCentredString(W/2,H-255,'Campo Bom • Rio Grande do Sul')
c.setFont('GI',11);c.drawCentredString(W/2,210,'Para a turma que constrói e sabe rir junto.')
s=ParagraphStyle('note',fontName='G',fontSize=9,leading=14,alignment=1)
p=Paragraph('Ficção criada a partir dos nomes e do argumento fornecidos pelo usuário. As situações e os diálogos foram inventados.',s);_,ph=p.wrap(W-100,100);p.drawOn(c,50,110-ph)
c.showPage();c.setFillColor(HexColor('#123b4f'));c.setFont('GB',24);c.drawString(43,H-65,'Sumário')
for i,(h,_) in enumerate(chap,1):
    y=H-102-(i-1)*28;c.setFont('G',9.5);c.drawString(43,y,h.replace(' — ','  '));c.drawRightString(W-43,y,str(starts[i]+3))
c.showPage();c.save()
c=canvas.Canvas(str(T/'back.pdf'),pagesize=(W,H));c.setFillColor(HexColor('#123b4f'));c.rect(0,0,W,H,fill=1,stroke=0)
c.setFillColor(HexColor('#f7eddb'));c.setFont('GB',25);c.drawCentredString(W/2,H-72,TITLE)
bs=ParagraphStyle('back',fontName='G',fontSize=12,leading=19,textColor=HexColor('#f7eddb'),spaceAfter=20)
y=H-112
for b in back:
    p=Paragraph(esc(b),bs);_,ph=p.wrap(W-100,H);p.drawOn(c,50,y-ph);y-=ph+20
assert y>35
c.showPage();c.save()
wr=PdfWriter()
for f in ['front','pre','body','back']:wr.append(str(T/(f+'.pdf')))
for i,(h,_) in enumerate(chap,1):wr.add_outline_item(h,starts[i]+2)
wr.add_metadata({'/Title':TITLE+' — '+SUB,'/Creator':'Preparação editorial com IA'})
with (R/'Mais uma obra.pdf').open('wb') as f:wr.write(f)

css='body{font-family:serif;line-height:1.5;margin:5%;}h1,h2{text-align:center;line-height:1.3;}p{text-indent:1.2em;margin:0 0 .5em;}p.d{text-indent:0;}img{max-width:100%;height:auto;}nav li{margin:.5em 0;}'
def xhtml(title,b):return '<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="pt-BR" xml:lang="pt-BR"><head><title>'+esc(title)+'</title><link rel="stylesheet" href="style.css"/></head><body>'+b+'</body></html>'
files={'OEBPS/style.css':css,'OEBPS/cover.xhtml':xhtml(TITLE,'<section epub:type="cover"><img src="cover.png" alt="Trabalhadores compartilhando café diante de uma casa em construção; Mais uma obra"/></section>'),'OEBPS/title.xhtml':xhtml(TITLE,'<h1>'+TITLE+'</h1><h2>'+SUB+'</h2><p class="d">Para a turma que constrói e sabe rir junto.</p><p class="d">Ficção. Situações e diálogos inventados a partir do argumento e dos nomes fornecidos.</p>')}
for i,(h,ps) in enumerate(chap,1):files[f'OEBPS/ch{i}.xhtml']=xhtml(h,'<section epub:type="chapter"><h1>'+esc(h)+'</h1>'+''.join('<p class="'+('d' if p.startswith('—') or j==0 else '')+'">'+esc(p)+'</p>' for j,p in enumerate(ps))+'</section>')
files['OEBPS/back.xhtml']=xhtml('Sobre a história','<h1>Sobre a história</h1>'+''.join('<p>'+esc(b)+'</p>' for b in back))
files['OEBPS/nav.xhtml']=xhtml('Sumário','<nav epub:type="toc" id="toc"><h1>Sumário</h1><ol>'+''.join(f'<li><a href="ch{i}.xhtml">{esc(h)}</a></li>' for i,(h,_) in enumerate(chap,1))+'</ol></nav>')
uid='urn:uuid:'+str(uuid.uuid5(uuid.NAMESPACE_URL,'mais-uma-obra-campo-bom-2026'))
manifest='<item id="img" href="cover.png" media-type="image/png" properties="cover-image"/><item id="css" href="style.css" media-type="text/css"/>'
manifest+=''.join(f'<item id="{a}" href="{a}.xhtml" media-type="application/xhtml+xml"'+(' properties="nav"' if a=='nav' else '')+'/>' for a in ['cover','title','nav']+[f'ch{i}' for i in range(1,17)]+['back'])
spine=''.join(f'<itemref idref="{a}"/>' for a in ['cover','title','nav']+[f'ch{i}' for i in range(1,17)]+['back'])
files['OEBPS/content.opf']=f'<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="pt-BR"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="uid">{uid}</dc:identifier><dc:title>{TITLE} — {SUB}</dc:title><dc:language>pt-BR</dc:language><meta property="dcterms:modified">2026-10-10T12:00:00Z</meta></metadata><manifest>{manifest}</manifest><spine>{spine}</spine></package>'
files['META-INF/container.xml']='<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'
with zipfile.ZipFile(R/'Mais uma obra.epub','w') as z:
    z.writestr('mimetype','application/epub+zip',compress_type=0)
    for n,v in files.items():z.writestr(n,v.encode('utf-8'),compress_type=8)
    z.write(R/'capa.png','OEBPS/cover.png',compress_type=8)
with zipfile.ZipFile(R/'Mais uma obra.epub') as z:
    assert z.testzip() is None
    assert z.infolist()[0].filename=='mimetype' and z.infolist()[0].compress_type==0
    for n in z.namelist():
        if n.endswith(('.xhtml','.xml','.opf')):
            t=ET.fromstring(z.read(n))
            for el in t.iter():
                for a in ['href','src']:
                    v=el.get(a)
                    if v:assert posixpath.normpath(posixpath.join(posixpath.dirname(n),v.split('#')[0])) in z.namelist()
    for i,(_,ps) in enumerate(chap,1):
        t=ET.fromstring(z.read(f'OEBPS/ch{i}.xhtml'));assert [''.join(p.itertext()) for p in t.findall('.//{http://www.w3.org/1999/xhtml}p')]==ps
reader=PdfReader(R/'Mais uma obra.pdf');assert len(reader.pages)==66
norm=lambda s:re.sub(r'\s+','',s)
pdft=norm('\n'.join(re.sub(r'^\d+\s*$', '',p.extract_text() or '',flags=re.M) for p in reader.pages))
for h,ps in chap:
    for p in ps:assert norm(p) in pdft,p[:80]
words=len(re.findall(r'\b\w+\b','\n'.join('\n'.join(ps) for _,ps in chap)))
report={'titulo':TITLE,'subtitulo':SUB,'capitulos':16,'palavras_narrativa':words,'minutos_a_250_palavras_por_minuto':round(words/250,1),'faixa_200_250_palavras_minuto':[round(words/250,1),round(words/200,1)],'paginas_totais_pdf':66,'paginas_narrativa_pdf':62,'fonte_corpo_pontos':round(size,3),'aberturas_capitulos':[starts[i]+3 for i in range(1,17)],'pdf_integridade_paragrafos':'PASSOU','epub_zip_xml_links_paragrafos':'PASSOU','epubcheck':'Não executado','kindle_previewer':'Não executado','autoria_assinatura':'Não informada; omitida'}
(R/'validacao.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'livro.html').write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>'+TITLE+'</title><style>'+css+'</style><h1>'+TITLE+'</h1><h2>'+SUB+'</h2>'+''.join('<section><h2>'+esc(h)+'</h2>'+''.join('<p>'+esc(p)+'</p>' for p in ps)+'</section>' for h,ps in chap),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
