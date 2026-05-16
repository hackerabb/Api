from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# السماح لصفحة الـ HTML بالوصول للموقع من أي مكان لمنع مشاكل الـ CORS
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET'
    return response

@app.route('/live')
def get_live_bets():
    try:
        # استقبال القسم المطلوب من الواجهة وافتراضياً كرة القدم (football)
        category = request.args.get('type', 'football').lower()
        
        # تحويل اسم القسم إلى المعرف الرقمي الخاص به في نظام 1xbet الخلفي
        sport_id = 1
        if category == 'basketball': sport_id = 2
        if category == 'tennis': sport_id = 4
        if category == 'cyber': sport_id = 100
        
        # الرابط الخلفي المباشر والخفيف لجلب البيانات بصيغة JSON
        url = f"https://1xbet.com/LiveFeed/Get1x2BaseSimpleView?sports={sport_id}&count=30&lng=en&mode=4"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        json_data = response.json()
        
        results = []
        
        if "Value" in json_data and isinstance(json_data["Value"], list):
            for game in json_data["Value"]:
                # جلب أسماء الفرق بأمان وضمان عدم وجود قيم فارغة
                team1 = game.get("O1E", "").strip()
                team2 = game.get("O2E", "").strip()
                odds_list = game.get("E", [])
                
                if team1 and team2 and isinstance(odds_list, list) and len(odds_list) >= 2:
                    try:
                        # جلب قيمة الأود الأول (W1)
                        o1 = odds_list[0].get("C", 0)
                        
                        # التمييز الذكي بين الرياضات ذات الـ 3 خيارات (كرة القدم) والـ 2 خيارات (التنس)
                        if len(odds_list) >= 3 and odds_list[1].get("T") == 2:
                            o2 = odds_list[2].get("C", 0)
                        else:
                            o2 = odds_list[1].get("C", 0)
                        
                        # تخطي المباراة إذا كانت الأودات غير متوفرة أو تساوي صفراً
                        if not o1 or not o2 or o1 <= 0 or o2 <= 0:
                            continue
                            
                        # احتساب التوقع والنسبة بناءً على الأود الأقل (الأقرب للفوز دائماً)
                        prediction = "W1" if o1 < o2 else "W2"
                        min_odd = min(o1, o2)
                        
                        # حساب نسبة النجاح للمباراة
                        prob = int(100 - (min_odd * 15))
                        prob = max(60, min(prob, 92)) # حصر النسبة بين 60% و 92% للحفاظ على المصداقية
                        
                        results.append({
                            "match": f"{team1} vs {team2}",
                            "odds1": str(round(o1, 2)),
                            "odds2": str(round(o2, 2)),
                            "prediction": prediction,
                            "probability": f"{prob}%"
                        })
                    except Exception:
                        continue
                        
        return jsonify({"status": "success", "category": category, "count": len(results), "results": results})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
