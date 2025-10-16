import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random
import io
from app.indexer import ScreenshotIndexer


def make_image(text: str, w: int = 640, h: int = 360) -> bytes:
    img = Image.new('RGB', (w, h), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    d.text((10, 10), text, fill=(0, 0, 0), font=font)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return buf.getvalue()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=str, default='./data')
    p.add_argument('--n', type=int, default=1000)
    p.add_argument('--recipes', type=int, default=0, help='number of recipe-like screenshots to bias in corpus')
    p.add_argument('--presentations', type=int, default=0, help='number of presentation/advice screenshots to bias')
    p.add_argument('--dogs', type=int, default=0, help='number of funny dog caption screenshots to bias')
    p.add_argument('--code', type=int, default=0, help='number of code/reference screenshots to bias')
    p.add_argument('--maps', type=int, default=0, help='number of map/directions screenshots to bias')
    p.add_argument('--chats', type=int, default=0, help='number of chat-like screenshots to bias')
    args = p.parse_args()

    data_dir = Path(args.out)
    idx = ScreenshotIndexer(data_dir=data_dir)

    templates = [
        "Booking PNR {code} for flight {num}",
        "Receipt Total ${amt}. Order {code}",
        "Chat with Alice at {time}",
        "Note: {code} due on {date}",
        "Article ref {code} amount ${amt}",
    ]

    recipe_templates = [
        "Recipe: {dish} — Ingredients: {ing1}, {ing2}, {ing3}. Steps: preheat, mix, bake.",
        "How to make {dish}: combine {ing1} and {ing2}, simmer {time} minutes.",
        "Best {dish} recipe — serve with {ing3}. Notes: {code}",
    ]

    pres_templates = [
        "Effective presentation tips: tell a story, {tip1}, {tip2}",
        "Slide structure: Problem, Solution, Impact. Use {tip1} and {tip2}",
        "Business advice: focus on audience, {tip1}, end with call-to-action",
    ]

    dog_templates = [
        "Funny dog on walk — caption: {caption} 🐶",
        "Spotted a goofy dog: {caption}",
        "Dog meme: {caption} #funnydog",
    ]

    code_templates = [
        "Code snippet: function add(a,b) {{ return a+b }} — example {code}",
        "Error: NullReferenceException at Foo.Bar() — fix: {tip1}",
        "Stack trace ref {code}: remember to {tip2}",
    ]

    map_templates = [
        "Directions: head north 2 mi, turn left. ETA {time}",
        "Route overview: {num} km total, via Main St.",
        "Map note: meet at park entry gate at {time}",
    ]

    chat_templates = [
        "Alice: let's meet at 3pm\nBob: ok sounds good\nYou: see you then",
        "DM — reminder: code {code} for pickup",
        "Group chat: presentation tips — {tip1} and {tip2}",
    ]

    def rand_code():
        import string
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

    def rand_amt():
        return f"{random.randint(5, 999)}.{random.randint(0,99):02d}"

    def rand_time():
        return f"{random.randint(1,12)}:{random.randint(0,59):02d} {'AM' if random.random()<0.5 else 'PM'}"

    def rand_date():
        return f"{random.randint(1,28)} Nov 2025"

    # Build a list of chosen templates according to requested biases
    chosen: list[str] = []
    for _ in range(max(0, args.recipes)):
        chosen.append(random.choice(recipe_templates).format(
            dish=random.choice(["pasta", "banana bread", "chicken curry", "tacos", "pancakes"]),
            ing1=random.choice(["flour", "eggs", "tomatoes", "garlic", "milk"]),
            ing2=random.choice(["salt", "pepper", "butter", "olive oil", "onion"]),
            ing3=random.choice(["basil", "cheese", "lemon", "rice", "cilantro"]),
            time=random.randint(5, 60),
            code=rand_code(),
        ))
    for _ in range(max(0, args.presentations)):
        chosen.append(random.choice(pres_templates).format(
            tip1=random.choice(["use visuals", "keep it simple", "practice" ]),
            tip2=random.choice(["limit bullets", "large fonts", "consistent theme"]),
        ))
    for _ in range(max(0, args.dogs)):
        chosen.append(random.choice(dog_templates).format(
            caption=random.choice(["zoomies engaged", "bonk", "silly floof", "heckin good boi"]) 
        ))
    for _ in range(max(0, args.code)):
        chosen.append(random.choice(code_templates).format(
            code=rand_code(), tip1=random.choice(["add null checks", "guard clauses", "retry with backoff"]), tip2=random.choice(["write tests", "simplify logic", "avoid globals"])
        ))
    for _ in range(max(0, args.maps)):
        chosen.append(random.choice(map_templates).format(
            time=rand_time(), num=random.randint(1, 120)
        ))
    for _ in range(max(0, args.chats)):
        chosen.append(random.choice(chat_templates).format(
            code=rand_code(), tip1=random.choice(["use visuals", "keep it simple", "practice" ]), tip2=random.choice(["limit bullets", "large fonts", "consistent theme"]) 
        ))

    # Fill the remainder with generic templates
    while len(chosen) < args.n:
        chosen.append(random.choice(templates).format(code=rand_code(), num=random.randint(10,9999), amt=rand_amt(), time=rand_time(), date=rand_date()))

    random.shuffle(chosen)

    for i in range(args.n):
        t = chosen[i]
        content = make_image(t)
        idx.index_image_bytes(content, filename=f"synthetic_{i}.jpg")
        if (i+1) % 100 == 0:
            print(f"Indexed {i+1}")
    idx.save()
    print("Done")


if __name__ == '__main__':
    main()


