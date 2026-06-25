from dotenv import load_dotenv
import anthropic
import base64
import json
import requests
import os
load_dotenv()
location = "Hockessin, Delaware, 19707"
ANALYZE_SCHEMA = {
    "type": "object",
    "properties": {
        "shopping_list": {"type": "array", "items": {"type": "string"}},
        "percent": {"type": "array", "items": {"type": "number"}},
        "reasoning": {"type": "string"},
    },
    "required": ["shopping_list", "percent", "reasoning"],
    "additionalProperties": False,
}

REFLECT_SCHEMA = {
    "type": "object",
    "properties": {
        "accept": {"type": "boolean"},
        "reason": {"type": "string"},
        "corrections": {"type": "array", "items": {"type": "string"}},
        "suggestion": {"type": "string"},
    },
    "required": ["accept", "reason", "corrections", "suggestion"],
    "additionalProperties": False,
}

SHOP_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "store": {"type": "string"},
                    "location": {"type": "string"},
                    "link": {"type": "string"},
                    "price": {"type": "number"},
                },
                "required": ["name", "store", "location", "link", "price"],
                "additionalProperties": False,
            },
        },
        "total_price": {"type": "number"},
    },
    "required": ["items", "total_price"],
    "additionalProperties": False,
}


def parse_json_message(message):
    """Return the JSON from the final text block of a response.

    Server tools (e.g. web_search) interleave server_tool_use /
    tool_result blocks before the final answer, so content[0] is not
    necessarily the text block — find the last text block instead.
    """
    text = next(
        (b.text for b in reversed(message.content) if b.type == "text"),
        None,
    )
    if text is None:
        raise ValueError(
            f"No text block in response (stop_reason={message.stop_reason}); "
            f"blocks={[b.type for b in message.content]}"
        )
    return json.loads(text)

def get_image(path):
    with open(path,"rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")
    
def image_analyze(model,image_data, feedback = None):
    content = [{
                "type":"image",
                "source":{
                    "type":"base64",
                    "media_type":"image/jpeg",
                    "data":image_data,
                },
            },{"type":"text","text":"""From this image, list every grocery 
               item you see here, list 100 percent confident first then items 
               that may be hard to see due to occlusion, angle, or obscure."""},
            ]
    if feedback:
        content.append({"type": "text",
            "text": f"Your previous analysis was rejected. Reviewer feedback: {feedback}\n"
                    f"Re-examine the images carefully addressing this before responding."
        })
    message = model.messages.create(
        model= "claude-haiku-4-5-20251001",
        max_tokens=1000,
        system="""You are a qualified deep professional image analyzer. Identify all grocery items.
        shopping_list: all items
        percent: corresponding confidence level (0-1) for each item
        reasoning: reasoning for each item""",
        output_config={"format": {"type": "json_schema", "schema": ANALYZE_SCHEMA}},
        messages=[
            {"role":"user","content": content}
        ])
    return parse_json_message(message)

def reflect(model, image_analyze_res, image_data):
    message = model.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        system="""You are a quality reviewer for grocery detection. You see the same
images the image agent saw, plus its analysis. Verify the analysis against the
actual images. Catch missed items, hallucinated items, and occluded items the
first pass may have gotten wrong.
accept: true or false
reason: brief explanation
corrections: any items the image agent got wrong
suggestion: what to re-examine if not accepted""",
        output_config={"format": {"type": "json_schema", "schema": REFLECT_SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": f"Verify from what you see to what image agent gave: {json.dumps(image_analyze_res)}"},
                ],
            }
        ],
    )
    return parse_json_message(message)

def reason(model,shop_list):
    pass

def shop(model, shop_list):
    findings = {}
    for item in shop_list:
        message = model.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system="""You are a grocery shopping research agent. Always perform a web
search to answer — never answer from memory. Find a store near the given location
that stocks the item and a realistic price.""",
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "allowed_domains":["instacart.com","acmemarkets.com","costco.com","bjs.com"],
                "max_uses": 1,
                "user_location": {
                    "type": "approximate",
                    "city": "Hockessin",
                    "region": "Delaware",
                    "country": "US",
                },
            }],
            messages=[{
                "role": "user",
                "content": f"Where can I buy {item} near {location}? "
                           f"Give a store and an approximate price.",
            }],
        )
        sources = []
        for block in message.content:
            if block.type == "web_search_tool_result" and isinstance(block.content, list):
                for r in block.content:
                    sources.append({"title": r.title, "link": r.url})

        used = getattr(message.usage, "server_tool_use", None)
        n = getattr(used, "web_search_requests", 0) if used else 0
        summary = "".join(b.text for b in message.content if b.type == "text")
        print(f"{item}: {n} searches, {len(sources)} real links")

        findings[item] = {"summary": summary, "sources": sources}

    format_msg = model.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system="""Format these findings into the schema, one entry PER GROCERY ITEM
(the dict key). `name` is the item, `store` is where to buy it, `price` is a number.
For `link`, you MUST copy one URL verbatim from that item's `sources` list. If that
item's `sources` list is empty, set `link` to an empty string. NEVER write, complete,
guess, or correct a URL yourself.""",
        output_config={"format": {"type": "json_schema", "schema": SHOP_SCHEMA}},
        messages=[{"role": "user", "content": f"Findings:\n{json.dumps(findings, indent=2)}"}],
    )
    return parse_json_message(format_msg)

def agents_pipeline(image_data):
    """Run analyze -> reflect (x3) -> shop.

    `image_data` is a base64-encoded image string (what image_analyze/reflect
    expect in the message "data" field). For local file testing, encode first
    with get_image(path).
    """
    image_agent = anthropic.Anthropic()
    reflective_agent = anthropic.Anthropic()
    shop_agent = anthropic.Anthropic()
    output = None
    feedback = None
    for i in range(3):
        output = image_analyze(image_agent,image_data,feedback)
        reflect_out = reflect(reflective_agent,output,image_data)
        if reflect_out["accept"]:
            break
        feedback = reflect_out["suggestion"]
    print(output)
    shopping_list = output["shopping_list"]
    final = shop(shop_agent,shopping_list)
    return {"inventory": output, "shopping": final}


    