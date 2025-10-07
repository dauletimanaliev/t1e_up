"""
Tie catalog with products
"""

TIES_CATALOG = [
    {
        'id': 'tie_001',
        'name': {
            'kz': 'Классикалық галстук №1',
            'ru': 'Классический галстук №1',
            'en': 'Classic Tie #1'
        },
        'description': {
            'kz': 'Элегантты галстук, іскерлік стиль үшін',
            'ru': 'Элегантный галстук для делового стиля',
            'en': 'Elegant tie for business style'
        },
        'price': 1000,
        'image': 'TieUp/11aa5e5e6196c36097eaae6d040ab151.webp',
        'material': '100% Natural Material'
    },
    {
        'id': 'tie_002',
        'name': {
            'kz': 'Галстук №2',
            'ru': 'Галстук №2',
            'en': 'Tie #2'
        },
        'description': {
            'kz': 'Заманауи дизайн',
            'ru': 'Современный дизайн',
            'en': 'Modern design'
        },
        'price': 1000,
        'image': 'TieUp/49b0c5337f0a4cab049faca97a0938ae.webp',
        'material': '100% Natural Material'
    },
    {
        'id': 'tie_003',
        'name': {
            'kz': 'Галстук №3',
            'ru': 'Галстук №3',
            'en': 'Tie #3'
        },
        'description': {
            'kz': 'Бизнес стиль',
            'ru': 'Бизнес стиль',
            'en': 'Business style'
        },
        'price': 1000,
        'image': 'TieUp/5474e6af70d8ed1516dc9896acc5451e.webp',
        'material': '100% Natural Material'
    },
    {
        'id': 'tie_004',
        'name': {
            'kz': 'Галстук №4',
            'ru': 'Галстук №4',
            'en': 'Tie #4'
        },
        'description': {
            'kz': 'Премиум сапа',
            'ru': 'Премиум качество',
            'en': 'Premium quality'
        },
        'price': 1000,
        'image': 'TieUp/54f2053123a61212aed740fe11e6193d.webp',
        'material': '100% Natural Material'
    },
    {
        'id': 'tie_005',
        'name': {
            'kz': 'Галстук №5',
            'ru': 'Галстук №5',
            'en': 'Tie #5'
        },
        'description': {
            'kz': 'Элегантты стиль',
            'ru': 'Элегантный стиль',
            'en': 'Elegant style'
        },
        'price': 1000,
        'image': 'TieUp/66c1d6551449a32f14cc88ae501b7071.webp',
        'material': '100% Natural Material'
    },
    {
        'id': 'tie_006',
        'name': {
            'kz': 'Галстук №6',
            'ru': 'Галстук №6',
            'en': 'Tie #6'
        },
        'description': {
            'kz': 'Мерекелік нұсқа',
            'ru': 'Праздничный вариант',
            'en': 'Festive option'
        },
        'price': 1000,
        'image': 'TieUp/841b83593a8af609e87759124cf5ec1b.webp',
        'material': '100% Natural Material'
    },
    {
        'id': 'tie_007',
        'name': {
            'kz': 'Галстук №7',
            'ru': 'Галстук №7',
            'en': 'Tie #7'
        },
        'description': {
            'kz': 'Күнделікті киім',
            'ru': 'Повседневный',
            'en': 'Casual wear'
        },
        'price': 1000,
        'image': 'TieUp/a0a1a0a307f4c5c41cf5987d166141eb.webp',
        'material': '100% Natural Material'
    },
    {
        'id': 'tie_008',
        'name': {
            'kz': 'Галстук №8',
            'ru': 'Галстук №8',
            'en': 'Tie #8'
        },
        'description': {
            'kz': 'Эксклюзивті дизайн',
            'ru': 'Эксклюзивный дизайн',
            'en': 'Exclusive design'
        },
        'price': 1000,
        'image': 'TieUp/df209d199876551bd7abf4516ee46db7.webp',
        'material': '100% Natural Material'
    },
    {
        'id': 'tie_009',
        'name': {
            'kz': 'Галстук №9',
            'ru': 'Галстук №9',
            'en': 'Tie #9'
        },
        'description': {
            'kz': 'Люкс класс',
            'ru': 'Люкс класс',
            'en': 'Luxury class'
        },
        'price': 1000,
        'image': 'TieUp/dff9ee5594129bda03a963b9c2d65612.webp',
        'material': '100% Natural Material'
    },
    {
        'id': 'tie_010',
        'name': {
            'kz': 'Галстук №10',
            'ru': 'Галстук №10',
            'en': 'Tie #10'
        },
        'description': {
            'kz': 'VIP дизайн',
            'ru': 'VIP дизайн',
            'en': 'VIP design'
        },
        'price': 1000,
        'image': 'TieUp/5474e6af70d8ed1516dc9896acc5451e (1).webp',
        'material': '100% Natural Material'
    },
    {
        'id': 'tie_011',
        'name': {
            'kz': 'Галстук №11',
            'ru': 'Галстук №11',
            'en': 'Tie #11'
        },
        'description': {
            'kz': 'Эксклюзив',
            'ru': 'Эксклюзив',
            'en': 'Exclusive'
        },
        'price': 1000,
        'image': 'TieUp/a0a1a0a307f4c5c41cf5987d166141eb (1).webp',
        'material': '100% Natural Material'
    }
]

def get_tie_by_id(tie_id: str):
    """Get tie by its ID"""
    for tie in TIES_CATALOG:
        if tie['id'] == tie_id:
            return tie
    return None

def format_tie_info(tie: dict, lang: str) -> str:
    """Format tie information for display"""
    from translations import get_text
    
    return (
        f"*{tie['name'][lang]}*\n\n"
        f"📝 {tie['description'][lang]}\n"
        f"🧵 {tie['material'][lang]}\n"
        f"💰 {get_text(lang, 'price')}: {tie['price']:,} {get_text(lang, 'currency')}\n"
    )
