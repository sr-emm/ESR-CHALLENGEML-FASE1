from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    vlans = []

    if request.method == "POST":
        vlan_ids = request.form.getlist("vlan_id")
        vlan_names = request.form.getlist("vlan_name")

        for vid, vname in zip(vlan_ids, vlan_names):
            vid = vid.strip()
            vname = vname.strip()

            if not vid:
                continue

            if not vname:
                vname = f"VLAN_{vid}"

            vlans.append({"id": vid, "name": vname})

        # En este punto, 'vlans' tiene lo que el usuario envió
        # y se lo devolvemos a la plantilla para que quede editable

    return render_template("index.html", vlans=vlans)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
