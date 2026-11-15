from flask import Flask, jsonify, request

app = Flask(__name__)


def calculate_alert_threshold(balance, minimum_balance):
    """Calcula a diferença entre o saldo e o limite mínimo configurado."""
    return balance - minimum_balance


@app.post("/monitoramento/limite")
def monitor_limit():
    data = request.get_json() or {}

    try:
        balance = float(data["balance"])
        minimum_balance = data["minimum_balance"]
        difference = calculate_alert_threshold(balance, minimum_balance)
        return jsonify({"difference": difference, "alert": difference < 0}), 200
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400


if __name__ == "__main__":
    app.run(debug=True)
