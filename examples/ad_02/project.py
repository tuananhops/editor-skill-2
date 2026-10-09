"""ad_02 — batch 2. Segment list from input/notes.md (cutting bot) + join fixes."""
SRC = 'input/ad_02.mp4'   # source footage (NOT in repo), relative to this project dir
CUT_REF = 'input/ad_02_cut.mp4'
FPS = '60000/1001'   # source was 59.94p (default when omitted: source fps)
OUT_NAME = 'ad_02_final.mp4'
def seg(a, b, **kw): return {'in': a, 'out': b, **kw}
SEGMENTS = [seg(2.15, 5.04), seg(8.935, 13.33, fade_in=0.012, note='-35 ms: MMS puts "bên" onset at 8.97, cut was on it'), seg(13.55, 17.35), seg(18.68, 19.87), seg(23.36, 25.29), seg(32.00, 36.79),
            seg(37.92, 39.41), seg(42.57, 44.82), seg(55.41, 59.61), seg(62.40, 64.10), seg(70.41, 71.95), seg(73.83, 75.33),
            seg(77.45, 78.44), seg(82.04, 86.69), seg(93.26, 98.80), seg(99.04, 100.26), seg(107.76, 110.40), seg(114.35, 118.12),
            seg(118.40, 121.89), seg(124.92, 127.86)]
ACCENT = (255, 79, 163)   # #FF4FA3: pink DJI mic transmitter, strongest colour in shot (overcast, same street as ad_01)
GRADE = ("eq=contrast=1.07:gamma=0.98,curves=master='0/0 0.10/0.085 0.5/0.5 0.80/0.78 0.92/0.87 1/0.93',"
         "huesaturation=saturation=-0.40:colors=g+c:strength=2,huesaturation=saturation=-0.15:colors=b+y:strength=1.5,"
         "colorbalance=rh=0.015:bh=-0.01,vignette=angle=0.30:mode=forward")

TEXT = [
    "Toàn bộ cái quy trình công việc phòng marketing thì bây giờ bên mình đã giao cho AI làm được hết rồi,",
    "từ việc là cắt ghép video, lên kịch bản, lên ý tưởng, ngay cả cái việc up video lên các nền tảng như TikTok, Facebook, YouTube thì AI có thể up được rồi.",
    "Và quan trọng là có hai công việc là mọi người nghĩ AI không làm được, đó chính là chốt sale,",
    "thay con người phải trực tin nhắn, trực page, trực Zalo để chốt sale.",
    "Thì bây giờ AI cũng làm được rồi.",
    "Mọi người có mong muốn có một phòng marketing tự động, mọi người đang có mong muốn làm công ty một người, thì bây giờ làm được rồi mọi người nhá.",
    "Bên công ty mình đã triển khai và đào tạo bot để tạo ra các bộ skill để giúp mọi người có thể làm được việc đấy.",
    "Anh em nào đang muốn tự động hóa, muốn AI làm việc cho mình, muốn cắt giảm nhân sự, muốn tiết kiệm chi phí để làm sao công ty phát triển hơn, mang lại lợi nhuận nhiều hơn,",
    "thì anh em hãy coi bên dưới, bên mình sẽ tặng cho anh em cái bộ skill đấy.",
    "Và quan trọng là anh em phải biết: đây là cái video mà mình đã cho AI edit hoàn toàn.",
    "Và thứ hai là video này sẽ được tự động up trên các nền tảng như TikTok, Facebook hoặc là YouTube, là AI có thể liên kết và up được hết rồi.",
    "Inbox cho mình ngay để bên mình tặng quà cho mọi người nhé.",
    "Cảm ơn mọi người rất nhiều.",
]

PAGES = """
Toàn bộ cái / *quy_trình
công việc / phòng *marketing
thì bây giờ / bên mình đã giao
cho *AI / ^làm_được_hết_rồi,
từ việc là / *cắt_ghép video,
lên *kịch_bản, / lên *ý_tưởng,
ngay cả cái việc / *up video
lên các nền tảng như
# platform names shown as chips overlay instead of captions
SKIP 3
thì *AI / có thể ^up_được_rồi.
Và quan trọng là
có *2 công việc / là mọi người nghĩ
*AI ^không / làm được,
đó chính là / *chốt_sale,
thay *con_người / phải
trực tin nhắn, / trực page, trực Zalo
để *chốt_sale.
Thì bây giờ / *AI cũng làm được rồi.
Mọi người / có mong muốn
có một phòng / *marketing ^tự_động,
mọi người đang có / mong muốn làm
*công_ty ^một_người,
thì bây giờ / ^làm_được_rồi mọi người nhá.
Bên công ty mình / đã *triển_khai và
*đào_tạo *bot / để tạo ra
các *bộ_skill / để giúp mọi người
có thể làm được / việc đấy.
Anh em nào / đang muốn
*tự_động_hóa,
muốn *AI / làm việc cho mình,
muốn *cắt_giảm / nhân sự,
muốn *tiết_kiệm / chi phí
để làm sao công ty / *phát_triển hơn,
mang lại / *lợi_nhuận nhiều hơn,
thì anh em / hãy coi *bên_dưới,
bên mình sẽ *tặng / cho anh em
cái *bộ_skill đấy.
Và quan trọng là / anh em ^phải_biết:
đây là cái video / mà mình đã cho
*AI ^edit / *hoàn_toàn.
Và thứ hai là / video này
sẽ được *tự_động *up / trên các nền tảng như
SKIP 5
là *AI có thể / ^liên_kết và
^up_được_hết_rồi.
*Inbox / cho mình ngay
để bên mình / *tặng_quà
cho mọi người nhé.
Cảm ơn mọi người / rất nhiều.
"""
CARDS = [
    dict(kind='list', t0='cắt@5|-0.15', t1='lên@8.6|-0.04', enter='slide_up', exit='flash', title='AI làm hết:', icon='check', row_size=140, dy=220, numbered=False,
         rows=[dict(text='cắt ghép video', at='cắt@5'), dict(text='kịch bản', at='kịch@6'), dict(text='ý tưởng', at='ý@6.5'), dict(text='up video', at='up@8')]),
    dict(kind='tools', t0='trực@16.7|-0.12', t1=20.47, enter='flash', exit='cut', title='Trước: người phải trực', title_size=64, title_gap=190,
         chip_size=80, chip_dy=230, y0=620,
         chips=[dict(text='tin nhắn', at='tin@16.9', strike_at='ai@19.5'), dict(text='page', at='page@17.4', strike_at='ai@19.5|0.08'),
                dict(text='Zalo', at='zalo@18', strike_at='ai@19.5|0.16')],
         result=dict(text='AI chốt sale', at='ai@19.5', size=170, y=1430)),
    dict(kind='pip', t0='phòng@21.6|-0.1', t1='thì@25.3|-0.04', exit='cut',
         labels=[('phòng marketing tự động', 'phòng@21.6'), ('công ty chỉ', 'công@24')],
         big=[dict(text='1 người', at='một@24.5', size=220)], pulse=['người@24.7']),
    dict(kind='list', t0=32.68, t1=37.34, enter='slide_left', exit='flash', title='Anh em nào đang muốn:', icon='check', row_size=130, dy=210, bg=2, numbered=False,
         rows=[dict(text='tự động hóa', at='tự@32.9'), dict(text='AI làm việc', at='ai@33.6'), dict(text='cắt giảm nhân sự', at='cắt@35'),
               dict(text='tiết kiệm chi phí', at='tiết@36.4')]),
]
OVERLAYS = [
    dict(kind='hook', t0=0.0, t1=3.9, base_y=400, gap=40, tokens=[
        dict(text='AI', font='serif9', size=250, color='accent', pulse_at='ai@3.5'),
        dict(text='làm hết', font='black', size=150, color='white')]),
    dict(kind='chips', texts=['TikTok', 'Facebook', 'YouTube'], at=['tiktok@9.5', 'facebook@10', 'youtube@10.5'], t0='tiktok@9.5|-0.05', t1=11.08, size=46, y=1500),
    dict(kind='chips', texts=['TikTok', 'Facebook', 'YouTube'], at=['tiktok@49.9', 'facebook@50.5', 'youtube@51.5'], t0='tiktok@49.9|-0.05', t1='là@52.2|-0.04', size=46, y=1500),
    dict(kind='cta', t0='inbox@54|-0.06', t1=56.94, text='Inbox để được tặng skill', y=1590),
]
PUNCH = [
    dict(t0='ai@3.5|-0.05', t1=4.55, z=1.18),
    dict(t0=12.26, t1=14.2, z=1.14),
    dict(t0='chốt@15.4|-0.06', t1=16.55, z=1.22),
    dict(t0='làm@25.9|-0.05', t1=26.93, z=1.18),
    dict(t0='thì@39.9|-0.05', t1=42.88, z=1.14),
    dict(t0=44.11, t1=46.75, z=1.2),
    dict(t0='là@52.2|-0.03', t1=54.0, z=1.16),
]
# music: HoliznaCC0 "Creature Comforts" (CC0, FMA): +13 dB drop at 102.84 s lands on "Inbox".
MUSIC = dict(path='music_creature-comforts.mp3', offset=102.84 - 54.10, under_lu=6.0)
CTA_HIT = 'inbox@54'
STILLS = [0.5, 2.0, 3.6, 4.3, 6.5, 8.4, 10.6, 13.0, 15.8, 17.6, 19.9, 22.5, 24.9, 26.4, 29.0, 31.0, 34.0, 36.9, 38.5, 41.0, 43.5, 45.5, 47.5, 50.8, 53.0, 54.8, 56.5]
