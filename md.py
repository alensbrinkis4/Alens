import os
import json
import google.generativeai as genai
from pathlib import Path

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
genai.configure(api_key=GEMINI_API_KEY)

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def load_prompt_template():
    try:
        return read_file('prompt.md')
    except FileNotFoundError:
       
        return """Analizē šo darba aprakstu (JD) un kandidāta CV, lai noteiktu atbilstību.

DARBA APRAKSTS:
{jd_text}

KANDIDĀTA CV:
{cv_text}

{{
  "match_score": 0-100,
  "summary": "Īss apraksts, cik labi CV atbilst JD.",
  "strengths": [
    "Galvenās prasmes/pieredze no CV, kas atbilst JD"
  ],
  "missing_requirements": [
    "Svarīgas JD prasības, kas CV nav redzamas"
  ],
  "verdict": "strong match | possible match | not a match"
}}

Esi precīzs un objektīvs. Fokusējies uz konkrētām prasmēm, pieredzi un kvalifikācijām."""

def evaluate_cv(jd_text, cv_text, prompt_template):
    """Izmanto Gemini Flash 2.5 lai novērtētu CV pret JD."""
    
    # Konfigurē modeli
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Sagatavo promptu
    prompt = prompt_template.format(jd_text=jd_text, cv_text=cv_text)
    
    # Ģenerē atbildi ar zemu temperatūru precizitātei
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json"
        )
    )
    
    # Parse JSON atbildi
    result = json.loads(response.text)
    return result

def generate_markdown_report(cv_num, result):
    
    verdict_emoji = {
        "strong match": "✅",
        "possible match": "⚠️",
        "not a match": "❌"
    }
    
    emoji = verdict_emoji.get(result['verdict'], "❓")
    
    report = f"""# CV{cv_num} Vērtējuma Pārskats

**Vērtējums:** {result['match_score']}/100  
**Nolēmums:** {emoji} {result['verdict'].upper()}

{result['summary']}

## Stiprās Puses
"""
    
    for strength in result['strengths']:
        report += f"- {strength}\n"
    
    report += "\n## Trūkstošās Prasības\n"
    
    if result['missing_requirements']:
        for missing in result['missing_requirements']:
            report += f"- {missing}\n"
    else:
        report += "*Nav identificētas būtiskas trūkstošas prasības.*\n"
    
    return report

def generate_html_report(cv_num, result):
    
    verdict_color = {
        "strong match": "#22c55e",
        "possible match": "#f59e0b",
        "not a match": "#ef4444"
    }
    
    color = verdict_color.get(result['verdict'], "#6b7280")
    
    strengths_html = "".join([f"<li>{s}</li>" for s in result['strengths']])
    missing_html = "".join([f"<li>{m}</li>" for m in result['missing_requirements']]) if result['missing_requirements'] else "<li><em>Nav identificētas būtiskas trūkstošas prasības.</em></li>"
    
    html = f"""<!DOCTYPE html>
<html lang="lv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CV{cv_num} Vērtējums</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1f2937;
            border-bottom: 3px solid {color};
            padding-bottom: 10px;
        }}
        .score {{
            font-size: 48px;
            font-weight: bold;
            color: {color};
            text-align: center;
            margin: 20px 0;
        }}
        .verdict {{
            background: {color};
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            text-transform: uppercase;
            margin: 20px 0;
        }}
        .summary {{
            background: #f9fafb;
            padding: 15px;
            border-left: 4px solid {color};
            margin: 20px 0;
            line-height: 1.6;
        }}
        h2 {{
            color: #374151;
            margin-top: 30px;
        }}
        ul {{
            line-height: 1.8;
        }}
        li {{
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>CV{cv_num} Vērtējuma Pārskats</h1>
        
        <div class="score">{result['match_score']}/100</div>
        <div class="verdict">{result['verdict']}</div>
        
        <div class="summary">
            <strong>Kopsavilkums:</strong><br>
            {result['summary']}
        </div>
        
        <h2>✨ Stiprās Puses</h2>
        <ul>
            {strengths_html}
        </ul>
        
        <h2>⚠️ Trūkstošās Prasības</h2>
        <ul>
            {missing_html}
        </ul>
    </div>
</body>
</html>"""
    
    return html

def main():
    Path("outputs").mkdir(exist_ok=True)
    Path("sample_inputs").mkdir(exist_ok=True)
    try:
        jd_text = read_file('sample_inputs/jd.txt')
        print("✓ Darba apraksts nolasīts")
    except FileNotFoundError:
        print("❌ Kļūda: sample_inputs/jd.txt nav atrasts!")
        return
    
    prompt_template = load_prompt_template()
    print("✓ Prompt template ielādēts")
    for i in range(1, 4):
        cv_file = f'sample_inputs/cv{i}.txt'
        
        try:
            print(f"\n📄 Apstrādāju CV{i}...")
            cv_text = read_file(cv_file)
            print(f"  ✓ CV{i} nolasīts")
            
            result = evaluate_cv(jd_text, cv_text, prompt_template)
            print(f"  ✓ Gemini analīze pabeigta")
            json_path = f'outputs/cv{i}.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"  ✓ Saglabāts: {json_path}")
            
            md_report = generate_markdown_report(i, result)
            md_path = f'outputs/cv{i}_report.md'
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_report)
            print(f"  ✓ Saglabāts: {md_path}")
            html_report = generate_html_report(i, result)
            html_path = f'outputs/cv{i}_report.html'
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_report)
            print(f"  ✓ Saglabāts: {html_path}")
            
            print(f"  📊 Rezultāts: {result['match_score']}/100 - {result['verdict']}")
            
        except FileNotFoundError:
            print(f"  ❌ Kļūda: {cv_file} nav atrasts!")
        except Exception as e:
            print(f"  ❌ Kļūda apstrādājot CV{i}: {str(e)}")
    
    print("\n✅ Visi CV apstrādāti! Rezultāti atrodami 'outputs/' direktorijā.")

if __name__ == "__main__":
    main()