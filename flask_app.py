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
    c.execute("DELETE FROM Genes WHERE Ensembl_Gene_ID =?", [id])
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

##################################################
#### API  = Application Programming Interface ####
##################################################
####     Prog Web pour la bioinformatique     ####
##################################################
####            Hermes Paraqindes             ####
##################################################
####            What it does :
####      GET method : /api/Gene/<id>         ####
#### It allows to represent the detailed information about the gene <id>
##################################################
####     DELETE method : /api/Genes/<id>      ####
#### It allows to delete the gene <id>
##################################################
#### These two methods are implemented in hte same function.
##################################################
##################################################
####       GET method : /api/Genes/           ####
##################################################
#### It shows a detailed information of top 100 genes ordered by gene ID
#### The user can use an offset to skip X genes
##################################################
####       POST method : /api/Genes/          ####
##################################################
#### It accepts a detailed information of one ar multiple genes.
#### Checks all the fields if they are in the needed format
#### It enters the gene in database and returns the url
##################################################
####       PUT method : /api/Genes/<id>       ####
##################################################
#### Accepts the same information as the POST method
#### If the gene exists, then it updates the new information filled
#### Else it creates a new gene



def connect_to_db():
    """This fonction allows to connect to the DATABASE.
    """
    db = sqlite3.connect(DATABASE)
    return db

@app.route("/api/Genes/<id>", methods = ['GET', 'DELETE'])
def api_gene_id(id):
    """This function check the methods used for /api/Genes/<id>. IN: gene id.
    If the method used is GET then a detailed information of the Gene is returned
    An extra information with the url of the gene is filled and all the transcripts
    If the method used id DELETE then the gene <id> will be delted.
    It will return the message that the gene <id> is deleted.
    In both methods, if the gene doesn't exist, then a message error is returned with 404 code
    """
    #db = sqlite3.connect(DATABASE)
    db = connect_to_db()
    c = db.cursor()
    colnames = []
    d = {}
    if request.method == 'GET':
        c.execute("SELECT * FROM Genes WHERE Ensembl_Gene_ID =?", [id])
        res = c.fetchone()
        if res:
            # dictionnary with key the column and values the information
            for i in c.description:
                colnames.append(i[0])
            d = dict(zip(colnames, res))
            # adding the url
            d["href"] = url_for('api_gene_id', id=d["Ensembl_Gene_ID"], _external = True)
            transcript = c.execute("SELECT Ensembl_Transcript_ID, Transcript_Start, Transcript_End FROM Transcripts WHERE Ensembl_Gene_ID =?", [id])
            tr_list = []
            for tr in transcript:
                tr_list.append(dict(zip([c[0] for c in transcript.description],tr)))
            # adding the transcripts information
            d["transcripts"] = tr_list
            out = jsonify(d)
        else:
            #return an error
            d["error"] = "Ce gène n'existe pas"
            out = jsonify(d)
            out.status_code=404
        connect_to_db().close()
    if request.method == 'DELETE':
        # dekete the gene if the gene exists. else return an error message
        c.execute("SELECT * FROM Genes WHERE Ensembl_Gene_ID =?", [id])
        res = c.fetchone()
        if res:
            c.execute("DELETE FROM Genes WHERE Ensembl_Gene_ID = ?", [id])
            db.commit()
            d["deleted"] = str(id) + " is deleted"
            out = jsonify(d)
            out.status_code = 200
        else:
            d["error"] = "Ce gène n'existe pas"
            out = jsonify(d)
            out.status_code=404

    return out

@app.route("/api/Genes/", methods = ['GET'])
def api_genes():
    """This function uses the GET method for the top 100 genes ordered by Ensembl_Gene_ID.
    It allows to choose an offset(integer) and skin X rows (genes). By default the offset = 0.
    It returns a detailed information about the genes without the transcripts information.
    The gene list is in Items. An URL with next or previous 100 genes is filled.
    """
    # get the offset value and check if is an integer
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
    # create a list of dictionnaries with all the genes
    for row in genes_api:
        genes_dict = dict(zip([c[0] for c in genes_api.description], row))
        genes_dict["href"] = url_for("api_gene_id", id=row[0], _external = True)
        genes_list.append(genes_dict)
    new_gene_dict = {}
    # create a new dictionnary with the genes, next, previous, first, and last
    new_gene_dict["items"] = genes_list
    new_gene_dict["first"] = offset + 1
    new_gene_dict["last"] = len(genes_list) + offset
    new_gene_dict["next"] = url_for("api_genes",_external=True) + "?offset=" + str(offset + 100)
    new_gene_dict["prev"] = url_for("api_genes",_external=True) + "?offset=" + str(offset)
    genes_out = jsonify(new_gene_dict)
    # return the new dictionnary
    return genes_out


def validate_json(data_json):
    """This function, given a data parameter, it will check if the data has a good format.
    If not, an error message with the appropriate status code will be returned.
    """
    # two lists with obligatory_fields and optionnal_fields for the Gene
    obligatory_fields=["Ensembl_Gene_ID","Chromosome_Name","Gene_Start","Gene_End"]
    optionnal_fields=["Band","Strand","Associated_Gene_Name"]
    # Check if data is a dict format.
    if isinstance(data_json,dict):
        # check if the fields of input data are instance of the datatable.
        for key in data_json.keys():
            if key not in obligatory_fields + optionnal_fields:
                msg = key + " is not an instance of this datatable. "
                #out = jsonify({"error": msg})
                status_code = 403
                return msg, status_code
        # check if all the obligatory_fields are filles
        for nedded_field in obligatory_fields:
            if nedded_field not in data_json.keys():
                    msg = nedded_field + " is nedded."
                    #out = jsonify({"error": msg})
                    status_code = 403
                    return msg, status_code
        # if an optionnal_fields is not completed, it will add a NONE value to it.
        for not_nedded_field in optionnal_fields:
            if not_nedded_field not in data_json.keys():
                data_json[not_nedded_field] = None

        # Get the information of the data
        ID = data_json["Ensembl_Gene_ID"]
        chr_name = data_json["Chromosome_Name"]
        gene_start = data_json["Gene_Start"]
        gene_end = data_json["Gene_End"]
        band = data_json["Band"]
        strand = data_json["Strand"]
        ass_gene_name = data_json["Associated_Gene_Name"]

        # check is Ensembl_Gene_ID is a string
        if not isinstance(ID, str):
            msg = "Ensembl_Gene_ID should be a string"
            #out = jsonify({"Type error": msg})
            status_code = 403
            #return msg, status_code
        # checks if Chromosome_Name is a string
        elif not isinstance(chr_name, str):
            msg = "Chromosome_Name should be a string"
            #out = jsonify({"Type error": msg})
            status_code = 403
            #return msg, status_code
        # check is Band is a string
        elif not isinstance(band, str) and band != None:
            msg = "Band should be a string"
            #out = jsonify({"Type error": msg})
            status_code = 403
            #return msg, status_code
        # checks if Associated_Gene_Name is a string
        elif not isinstance(ass_gene_name, str) and ass_gene_name != None:
            msg = "Associated_Gene_Name should be a string"
            #out = jsonify({"Type error": msg})
            status_code = 403
            #return msg, status_code

        # checks if gene start is an integer
        elif not isinstance(gene_start, int):
            msg = "Gene_Start should be an integer"
            #out = jsonify({"Type error": msg})
            status_code = 403
            #return out, status_code
        # checks if Gene_End is an integer
        elif not isinstance(gene_end, int):
            msg = "Gene_End should be an integer"
            #out = jsonify({"Type error": msg})
            status_code = 403
            #return out, status_code
        # Checks if Gene_End is higher than Gene_Start
        elif gene_start > gene_end:
            msg = "Gene_Start cannot be higher than Gene_End"
            #out = jsonify({"Type Error": msg})
            status_code = 416
            #return msg, status_code
        # Checks if the Strand is an integer and equal to -1 or 1
        elif not isinstance(strand, int) and  strand != None and strand not in [-1,1]:
            msg = "Strand should be an integer : -1 for complementary strand and 1 for matrice brand"
            #out = jsonify({"Type Error": msg})
            status_code = 403
            #return msg, status_code

        else:
            #db = connect_to_db()
            #db.execute("""
            #  INSERT INTO Genes
            #  (Ensembl_Gene_ID, Chromosome_Name, Band, Strand, Gene_Start,
            #   Gene_End,Associated_Gene_Name)
            #  VALUES (?,?,?,?,?,?,?)
            #  """, [ID,chr_name,band,strand,gene_start,gene_end,ass_gene_name])
            #c.execute("INSERT INTO Genes (Ensembl_Gene_ID, Chromosome_Name, Band, Strand, Gene_Start, Gene_End, Associated_Gene_Name, Transcript_Count) VALUES (?,?,?,?,?,?,?,?)",(gene_id,chr_name,band,strand,start,end,asso,count))
            #db.commit()
            #msg = url_for('api_gene_id', id=ID, _external = True)
            #out = jsonify({"created": msg})
            #out.status_code = 201
            #return out
            #msg = url_for('api_gene_id', id=i["Ensembl_Gene_ID"], _external = True)
            #status_code

            #return TRUE if the data is good
            return True
        # return the error message and status_code if the data is not good
        return msg, status_code


def create_a_gene(data_dict):
    # given a well formated data, it creates a new gene in the database
    db = connect_to_db()
    db.execute("""INSERT INTO Genes (Ensembl_Gene_ID, Chromosome_Name, Band, Strand, Gene_Start, Gene_End,Associated_Gene_Name)
        VALUES (?,?,?,?,?,?,?)""",
        [data_dict["Ensembl_Gene_ID"], data_dict["Chromosome_Name"], data_dict["Band"], data_dict["Strand"], data_dict["Gene_Start"],data_dict["Gene_End"],data_dict["Associated_Gene_Name"]])
    db.commit()


@app.route("/api/Genes/", methods = ['POST'])
def api_post_gene():
    """This function gets the data information with POST method. Checks if the data is well formated.
    If yes it will return the url for all the genes created. If not it will retrun the error message.
    It can accept a gene or a list of genes.
    """
    # get the json format of data
    json_post = request.get_json()
    # turned in a list if there are multiple genes given
    json_post = [json_post]
    # this was for testing. If no json format given, it allowed me to check if the code function.
    if not json_post:
        json_post = [{
          "Associated_Gene_Name": "TSPAN6",
          "Band": "q22.1",
          "Chromosome_Name": "X",
          "Ensembl_Gene_ID": "ENSG00000000003",
          "Gene_End": 99894988,
          "Gene_Start": 99883667,
          "Strand": -1
        },
        {
          "Associated_Gene_Name": "TNMD",
          "Band": "q22.1",
          "Chromosome_Name": "X",
          "Ensembl_Gene_ID": "ENSG00000000005",
          "Gene_End": 99854882,
          "Gene_Start": 99839799,
          "Strand": -1
        }]
    #print(json_post.keys())
    #validate_json(json_post)
    url = []
    for i in json_post:
        # for each gene given, checks if is well formated and returns the url of the new gene.
        if validate_json(i) == True:
            # create the new gene
            create_a_gene(i)
            msg = url_for('api_gene_id', id=i["Ensembl_Gene_ID"], _external = True)
            url.append(msg)
            out = jsonify({"url_created": msg})
            out.status_code = 201
        else:
            # return the error message
            msg, status_code = validate_json(i)
            out = jsonify({"error": msg + " pour le gene " + str(i)})
            out.status_code = status_code
            return out
    # returns the url for the new genes created
    return jsonify({"url": url}) #validate_json(json_post)#str(json_post)


def update_gene_api(data_dict, id):
    """This function, given a well formated data and the gene id, it allows to update an existed gene with
    the new informatio
    """
    db = connect_to_db()
    db.execute("""UPDATE Genes
SET Band = ?, Chromosome_Name = ?, Strand  = ?, Gene_Start = ?, Gene_End = ?, Associated_Gene_Name = ?
WHERE Ensembl_Gene_ID = ?""",[data_dict["Band"], data_dict["Chromosome_Name"], data_dict["Strand"], data_dict["Gene_Start"], data_dict["Gene_End"],data_dict["Associated_Gene_Name"],id])
    db.commit()

@app.route("/api/Genes/<id>", methods = ['PUT'])
def put_api_gene(id):
    """This funciton, given a gene id, allows to update an existed gene with the new information or to
    create a new one.
    """
    # get the data
    json_put = request.get_json()
    # turned in a list
    json_put = [json_put]
    #if multiple genes given
    for i in json_put:
        # the id in the json data should be the same with the id given in the url
        i_id = i["Ensembl_Gene_ID"]
        if i_id != id:
            msg = "L'url " + id + " correspond pas à votre Ensembl_Gene_ID " + i_id
            out = jsonify({"error": msg})
            out.status_code = 400
            return out
        else:
            # checks if the data is well formated
            if validate_json(i) == True:
                db = connect_to_db()
                c = db.cursor()
                c.execute("SELECT * FROM Genes WHERE Ensembl_Gene_ID =?", [id])
                res = c.fetchone()
                # if the gene exist then udpate the gene with the new information
                # return the updated message
                if res:
                    db.close()
                    update_gene_api(i, i_id)
                    msg = i["Ensembl_Gene_ID"] + " gene is updated to " + url_for('api_gene_id', id = i["Ensembl_Gene_ID"], _external = True)
                    out = jsonify({"updated": msg})
                    out.status_code = 200
                else:
                    # else, create the new gene and return the url for the new gene
                    db.close()
                    create_a_gene(i)
                    msg = url_for('api_gene_id', id=i["Ensembl_Gene_ID"], _external = True)
                    out = jsonify({"Gene_created": msg})
                    out.status_code = 201

            else:
                # if data is not well formated, return the error message
                msg, status_code = validate_json(i)
                out = jsonify({"error": msg + " pour le gene " + str(i)})
                out.status_code = status_code
                return out


            return out






if __name__ == "__main__":
    app.run(debug=True)
