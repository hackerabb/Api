from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# المفتاح الخاص بك تم دمجه بنجاح هنا
API_KEY = "e91d644564bb177175b5c6dfef6b0db9"

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET'
    return response

@app.route('/live')
def get_live_bets():
    try:
        category = request.args.get('type', 'football').lower()
        
        # تحديد القسم المطلق بناءً على طلب المستخدم
        sport_key = "soccer_epl"  # كرة القدم الافتراضية
        if category == "basketball": sport_key = "basketball_nba"
        if category == "tennis": sport_key = "tennis_atp"
        
        # رابط جلب البيانات الحية الآمن بدون حظر من Vercel
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h"
        
        response = requests.get(url, timeout=10)
        json_data = response.json()
        
        results = []
        
        if isinstance(json_data, list):
            for game in json_data:
                team1 = game.get("home_team", "")
                team2 = game.get("away_team", "")
                bookmakers = game.get("bookmakers", [])
                
                if team1 and team2 and bookmakers:
                    markets = bookmakers[0].get("markets", [])
                    if markets:
                        outcomes = markets[0].get("outcomes", [])
                        if len(outcomes) >= 2:
                            try:
                                o1 = outcomes[0].get("price", 0)
                                o2 = outcomes[1].get("price", 0)
                                
                                prediction = "W1" if o1 < o2 else "W2"
                                min_odd = min(o1, o2)
                                
                                prob = int(100 - (min_odd * 15))
                                prob = max(60, min(prob, 92))
                                
                                results.append({
                                    "match": f"{team1} vs {team2}",
                                    "odds1": str(o1),
                                    "odds2": str(o2),
                                    "prediction": prediction,
                                    "probability": f"{prob}%"
                                })
                            except Exception:
                                continue
                                
        return jsonify({"status": "success", "category": category, "count": len(results), "results": results})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
