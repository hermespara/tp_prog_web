#!/usr/bin/python3.5

from flask import *
import jinja2
import sqlite3


DATABASE = "/home/hermes/Bureau/S3/Web pour la bioinfo/TP_2/tp_prog_web/ensembl_hs63_simple.sqlite"

app = Flask(__name__)


def getAllGenes():
    db = sqlite3.connect(DATABASE)
    c = db.cursor()
    c.execute('SELECT Ensembl_Gene_ID,Associated_Gene_Name FROM Genes LIMIT 1000')
    res = c.fetchall()
    db.close()
    return res

def info_gene(id):
    db = sqlite3.connect(DATABASE)
    c = db.cursor()
    c.execute("SELECT * FROM Genes WHERE Ensembl_Gene_ID =?", [id])
    res = c.fetchall()
    colnames = []
    for i in c.description:
        colnames.append(i[0])
    db.close()
    return [colnames,res]

def info_transcrit(id):
    db = sqlite3.connect(DATABASE)
    c = db.cursor()
    c.execute("SELECT Ensembl_Transcript_ID, Transcript_Start, Transcript_End FROM Transcripts WHERE Ensembl_Gene_ID =?", [id])
    res = c.fetchall()
    colnames = []
    for i in c.description:
        colnames.append(i[0])
    db.close()
    return [colnames,res]

@app.route("/")
def root():
    return render_template("root.html")


@app.route("/Genes")
def Genes():
    genes_all = getAllGenes()
    return render_template("Genes.html", title="Bienvenue", res=genes_all)

@app.route("/Genes/view/<id>")
def view(id):
    gene_info_id = info_gene(id)
    transcript_info = info_transcrit(id)
    return render_template("view_id.html", colnames = gene_info_id[0], gene_id=gene_info_id[1], colnames_transcrit=transcript_info[0], transcrit_info=transcript_info[1])

@app.route("/Genes/del/<id>", methods=['POST'])
def del_id(id):
    db = sqlite3.connect(DATABASE)
    c = db.cursor()
    c.execute("DELETE FROM Genes WHERE Ensembl_Gene_ID ='%s'" % id)
    db.commit()
    return redirect(url_for("Genes"))

@app.route("/Genes/new", methods=["POST", "GET"])
def new():
    if request.method == "POST":
        gene_id = request.form.get("Ensembl_Gene_ID")
        if not gene_id:
            abort(400, "Ensembl_Gene_ID ne doit pas etre vide")
        chr_name = request.form.get("Chromosome_Name")
        band = request.form.get("Band")
        strand = request.form.get("Stand")
        start = request.form.get("Gene_Start")
        end = request.form.get("Gene_End")
        asso = request.form.get("Associated_Gene_Name")
        count = request.form.get("Transcript_Count")

        db = sqlite3.connect(DATABASE)
        c = db.cursor()
        db.execute("""
          INSERT INTO Genes
          (Ensembl_Gene_ID, Chromosome_Name, Band, Strand, Gene_Start,
           Gene_End,Associated_Gene_Name, Transcript_Count)
          VALUES (?,?,?,?,?,?,?,?)
          """, [gene_id,chr_name,band,strand,start,end,asso,count])
        #c.execute("INSERT INTO Genes (Ensembl_Gene_ID, Chromosome_Name, Band, Strand, Gene_Start, Gene_End, Associated_Gene_Name, Transcript_Count) VALUES (?,?,?,?,?,?,?,?)",(gene_id,chr_name,band,strand,start,end,asso,count))
        db.commit()
        return redirect(url_for("new"))
    else:
        return render_template('new_genes.html')

#### API  = Application Programming Interface ####

@app.route("/api/Genes/<id>", methods = ['GET'])
def api_gene_id(id):
    db = sqlite3.connect(DATABASE)
    c = db.cursor()
    c.execute("SELECT * FROM Genes WHERE Ensembl_Gene_ID =?", [id])
    res = c.fetchone()
    colnames = []
    d = {}
    if res:
        for i in c.description:
            colnames.append(i[0])
        d = dict(zip(colnames, res))
        transcript = c.execute("SELECT Ensembl_Transcript_ID, Transcript_Start, Transcript_End FROM Transcripts WHERE Ensembl_Gene_ID =?", [id])
        for a in transcript:
            d["transcripts"] = [dict(zip([c[0] for c in transcript.description], a))]
        out = jsonify(d)
    else:
        d["error"] = "Ce gène n'existe pas"
        out = jsonify(d)
        out.status_code=404
    db.close()
    return out

@app.route("/api/Genes/", methods = ['GET'])
def api_genes():
    print("hello")
    offset=request.args.get("offset")
    if not offset:
        offset = 0
    try:
        offset=int(offset)
    except ValueError:
            abort(400, "offset should be an integer")
    db = sqlite3.connect(DATABASE)
    c = db.cursor()
    genes_api = c.execute("""
          SELECT Ensembl_Gene_ID,Associated_Gene_Name, Chromosome_Name, Band, Strand, Gene_End, Gene_Start, Transcript_count
          FROM Genes
          ORDER BY Ensembl_Gene_ID
          LIMIT 100
          OFFSET ?
        """,[offset])

    genes_list = []
    gene_dict = {}
    for row in genes_api:
        genes_dict = [dict(zip([c[0] for c in genes_api.description], row))]
        genes_list.append(genes_dict)
    new_gene_dict = {}
    new_gene_dict["items"] = genes_list
    new_gene_dict["first"] = offset + 1
    new_gene_dict["last"] = len(genes_list)
    new_gene_dict["next"] = url_for("api_genes",_external=True) + "?offset" + str(offset + 100)
    new_gene_dict["prev"] = url_for("api_genes",_external=True) + "?offset=" + str(offset)
    genes_out = jsonify(new_gene_dict)
    return genes_out


def validate_json(data_json):

    obligatory_fields=["Ensembl_Gene_ID","Chromosome_Name","Gene_Start","Gene_End"]
    optionnal_fields=["Band","Strand","Associated_Gene_Name"]
    print(data_json.keys())
    # Check if data is a dict format.
    if isinstance(data_json,dict):
        # check if the fields of input data are instance of the datatable.
        for key in data_json.keys():
            print(key)
            if key not in obligatory_fields + optionnal_fields:
                msg = key + " is not an instance of this datatable. "
                out = jsonify({"error": msg})
                out.status_code = 403
                return out

        for nedded_field in obligatory_fields:
            if nedded_field not in data_json.keys():
                    msg = nedded_field + " is nedded."
                    out = jsonify({"error": msg})
                    out.status_code = 403
                    return out

        for not_nedded_field in optionnal_fields:
            if not_nedded_field not in data_json.keys():
                data_json[not_nedded_field] = None


        ID = data_json["Ensembl_Gene_ID"]
        chr_name = data_json["Chromosome_Name"]
        gene_start = data_json["Gene_Start"]
        gene_end = data_json["Gene_End"]
        band = data_json["Band"]
        strand = data_json["Strand"]
        ass_gene_name = data_json["Associated_Gene_Name"]

        if not isinstance(ID, str):
            msg = "Ensembl_Gene_ID should be a string"
            out = jsonify({"Type error": msg})
            out.status_code = 403
            return out
        elif not isinstance(chr_name, str):
            msg = "Chromosome_Name should be a string"
            out = jsonify({"Type error": msg})
            out.status_code = 403
            return out
        elif not isinstance(band, str) and band != None:
            msg = "Band should be a string"
            out = jsonify({"Type error": msg})
            out.status_code = 403
            return out

        elif not isinstance(ass_gene_name, str) and ass_gene_name != None:
            msg = "Associated_Gene_Name should be a string"
            out = jsonify({"Type error": msg})
            out.status_code = 403
            return out

        elif not isinstance(gene_start, int):
            msg = "Gene_Start should be an integer"
            out = jsonify({"Type error": msg})
            out.status_code = 403
            return out
        elif not isinstance(gene_end, int):
            msg = "Gene_End should be an integer"
            out = jsonify({"Type error": msg})
            out.status_code = 403
            return out
        elif gene_start > gene_end:
            msg = "Gene_Start cannot be higher than Gene_End"
            out = jsonify({"Type Error": msg})
            out.status_code = 416
            return out
        elif not isinstance(strand, int) and  strand != None and strand not in [-1,1]:
            msg = "Strand should be an integer : -1 for complementary strand and 1 for matrice brand"
            out = jsonify({"Type Error": msg})
            out.status_code = 403
            return out





        return jsonify(data_json)



@app.route("/api/Genes/", methods = ['POST'])
def api_post_gene():
    json_post = request.get_json()
    #print(json_post.keys())
    #validate_json(json_post)
    return validate_json(json_post)#str(json_post)



if __name__ == "__main__":
    app.run(debug=True)
