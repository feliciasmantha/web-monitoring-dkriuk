import os
from flask import Flask, render_template, request, redirect, session
from database import get_connection
from datetime import date
from flask import send_file
from openpyxl import Workbook
from openpyxl.styles import Font
import io

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

##LOGINNN

@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id,nama,role
            FROM users
            WHERE username=%s
            AND password=%s
        """,(username,password))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:

            session["id"] = user[0]
            session["nama"] = user[1]
            session["role"] = user[2]

            if session["role"] == "owner":
                return redirect("/dashboard_owner")

            if session["role"] == "karyawan":
                return redirect("/dashboard_karyawan")

            if session["role"] == "supplier":
                return redirect("/dashboard_supplier")

        return render_template(
    "auth/login.html",
    error="Username atau Password Salah"
)   

    return render_template("auth/login.html")

## LOGOUTTT

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

## DASH OWNERRR

@app.route("/dashboard_owner")
def dashboard_owner():

    if "id" not in session:
        return redirect("/")

    if session["role"] != "owner":
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM bahan_baku")
    total_bahan = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM supplier")
    total_supplier = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM permintaan
        WHERE status='Menunggu'
    """)
    permintaan = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM bahan_baku
        WHERE stok <= stok_minimum
    """)
    stok_minimum = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
    "owner/dashboard_owner.html",
    total_bahan=total_bahan,
    total_supplier=total_supplier,
    permintaan=permintaan,
    stok_minimum=stok_minimum
)
## DASH KARYAWANNN

@app.route("/dashboard_karyawan")
def dashboard_karyawan():

    if "id" not in session:
        return redirect("/")

    if session["role"] != "karyawan":
        return redirect("/")

    conn=get_connection()
    cur=conn.cursor()

    cur.execute("SELECT COUNT(*) FROM bahan_baku")
    total_bahan=cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM supplier")
    total_supplier=cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM stok_masuk")
    stok_masuk=cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM stok_keluar")
    stok_keluar=cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
    "karyawan/dashboard_karyawan.html",
        total_bahan=total_bahan,
        total_supplier=total_supplier,
        stok_masuk=stok_masuk,
        stok_keluar=stok_keluar
    )

## DASH SUPPLIERRR

@app.route("/dashboard_supplier")
def dashboard_supplier():

    if "id" not in session or session["role"] != "supplier":
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM permintaan p
        JOIN supplier s
            ON s.id=p.supplier_id
        WHERE s.user_id=%s
    """,(session["id"],))

    total = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM permintaan p
        JOIN supplier s
            ON s.id=p.supplier_id
        WHERE s.user_id=%s
        AND status='Menunggu'
    """,(session["id"],))

    menunggu = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM permintaan p
        JOIN supplier s
            ON s.id=p.supplier_id
        WHERE s.user_id=%s
        AND status='Disetujui'
    """,(session["id"],))

    selesai = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        "supplier/dashboard_supplier.html",
        total=total,
        menunggu=menunggu,
        selesai=selesai
    )

# ==========================
# CRUD BAHAN BAKU
# ==========================

@app.route("/bahan", methods=["GET","POST"])
def bahan():

    if "id" not in session or session["role"] != "karyawan":
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        nama = request.form["nama_bahan"]
        satuan = request.form["satuan"]
        stok = request.form["stok"]
        minimum = request.form["stok_minimum"]

        cur.execute("""
        INSERT INTO bahan_baku
        (nama_bahan,satuan,stok,stok_minimum)
        VALUES(%s,%s,%s,%s)
        """,(nama,satuan,stok,minimum))

        conn.commit()

        return redirect("/bahan")

    cur.execute("""
        SELECT *
        FROM bahan_baku
        ORDER BY id
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
    "karyawan/bahan.html",
    data=data
)

## EDIT BAHAANNN

@app.route("/edit_bahan/<int:id>", methods=["GET","POST"])
def edit_bahan(id):

    if "id" not in session or session["role"] != "karyawan":
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        nama = request.form["nama_bahan"]
        satuan = request.form["satuan"]
        stok = request.form["stok"]
        minimum = request.form["stok_minimum"]

        cur.execute("""
            UPDATE bahan_baku
            SET
                nama_bahan=%s,
                satuan=%s,
                stok=%s,
                stok_minimum=%s
            WHERE id=%s
        """, (nama, satuan, stok, minimum, id))

        conn.commit()

        cur.close()
        conn.close()

        return redirect("/bahan")

    cur.execute("""
        SELECT *
        FROM bahan_baku
        WHERE id=%s
    """, (id,))

    data = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "karyawan/edit_bahan.html",
        data=data
    )

## hapus bahan

@app.route("/hapus_bahan/<int:id>")
def hapus_bahan(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM permintaan WHERE bahan_id=%s",
        (id,)
    )

    jumlah = cur.fetchone()[0]

    if jumlah > 0:
        cur.close()
        conn.close()
        return "Bahan tidak dapat dihapus karena masih digunakan pada data permintaan."

    cur.execute(
        "DELETE FROM bahan_baku WHERE id=%s",
        (id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/bahan")

# ==========================
# CRUD SUPPLIER
# ==========================

@app.route("/supplier", methods=["GET", "POST"])
def supplier():

    if "id" not in session or session["role"] != "karyawan":
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        nama = request.form["nama_supplier"]
        telepon = request.form["telepon"]
        alamat = request.form["alamat"]
        email = request.form["email"]

        cur.execute("""
            INSERT INTO supplier
            (nama_supplier, telepon, alamat, email)
            VALUES (%s, %s, %s, %s)
        """, (nama, telepon, alamat, email))

        conn.commit()

        return redirect("/supplier")

    cur.execute("""
        SELECT *
        FROM supplier
        ORDER BY id
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "karyawan/supplier.html",
        data=data
    )


@app.route("/edit_supplier/<int:id>",methods=["GET","POST"])
def edit_supplier(id):

    if "id" not in session or session["role"]!="karyawan":
        return redirect("/")

    conn=get_connection()
    cur=conn.cursor()

    if request.method=="POST":

        nama=request.form["nama_supplier"]
        telepon=request.form["telepon"]
        alamat=request.form["alamat"]
        email=request.form["email"]

        cur.execute("""
        UPDATE supplier
        SET
        nama_supplier=%s,
        telepon=%s,
        alamat=%s,
        email=%s
        WHERE id=%s
        """,(nama,telepon,alamat,email,id))

        conn.commit()

        cur.close()
        conn.close()

        return redirect("/supplier")

    cur.execute("""
    SELECT *
    FROM supplier
    WHERE id=%s
    """,(id,))

    data=cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "karyawan/edit_supplier.html",
        data=data
    )


@app.route("/hapus_supplier/<int:id>")
def hapus_supplier(id):

    if "id" not in session or session["role"]!="karyawan":
        return redirect("/")

    conn=get_connection()
    cur=conn.cursor()

    cur.execute("""
    DELETE
    FROM supplier
    WHERE id=%s
    """,(id,))

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/supplier")

# ==========================
# PERMINTAAN OWNER
# ==========================

@app.route("/permintaan", methods=["GET", "POST"])
def permintaan():

    if "id" not in session or session["role"] != "owner":
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        supplier = request.form["supplier"]
        bahan = request.form["bahan"]
        jumlah = request.form["jumlah"]
        tanggal = request.form["tanggal"]      # pastikan ada di form
        catatan = request.form["catatan"]

        cur.execute("""
            INSERT INTO permintaan
            (
                supplier_id,
                bahan_id,
                jumlah,
                tanggal,
                status,
                catatan
            )
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            supplier,
            bahan,
            jumlah,
            tanggal,
            "Menunggu",
            catatan
        ))

        conn.commit()

        return redirect("/permintaan")

    cur.execute("""
        SELECT id,nama_supplier
        FROM supplier
        ORDER BY nama_supplier
    """)

    supplier = cur.fetchall()

    cur.execute("""
        SELECT id,nama_bahan
        FROM bahan_baku
        ORDER BY nama_bahan
    """)

    bahan = cur.fetchall()

    cur.execute("""
        SELECT

            p.id,
            s.nama_supplier,
            b.nama_bahan,
            p.jumlah,
            p.tanggal,
            p.status,
            p.catatan

        FROM permintaan p

        JOIN supplier s
            ON s.id = p.supplier_id

        JOIN bahan_baku b
            ON b.id = p.bahan_id

        ORDER BY p.id DESC
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "owner/permintaan.html",
        supplier=supplier,
        bahan=bahan,
        data=data
    )
## PERMINTAAN SUPPLIERRR

@app.route("/permintaan_supplier", methods=["GET", "POST"])
def permintaan_supplier():

    if "id" not in session or session["role"] != "supplier":
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    # Update status
    if request.method == "POST":

        permintaan_id = request.form["permintaan_id"]
        status = request.form["status"]

        cur.execute("""
            UPDATE permintaan
            SET status=%s
            WHERE id=%s
        """, (status, permintaan_id))

        conn.commit()

        return redirect("/permintaan_supplier")

    # Ambil hanya permintaan untuk supplier yang login
    cur.execute("""
        SELECT
            p.id,
            b.nama_bahan,
            p.jumlah,
            p.tanggal,
            p.status,
            p.catatan

        FROM permintaan p

        JOIN supplier s
            ON s.id = p.supplier_id

        JOIN bahan_baku b
            ON b.id = p.bahan_id

        WHERE s.user_id = %s

        ORDER BY p.id DESC
    """, (session["id"],))

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "supplier/permintaan_supplier.html",
        data=data
    )

# ==========================
# MONITORING STOK
# ==========================

@app.route("/monitoring")
def monitoring():

    if "id" not in session:
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""

    SELECT
        id,
        nama_bahan,
        satuan,
        stok,
        stok_minimum,

        CASE
            WHEN stok <= stok_minimum
            THEN 'Minimum'

            ELSE 'Aman'
        END

    FROM bahan_baku

    ORDER BY nama_bahan

    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "owner/monitoring.html",
        data=data
    )

## STOK MASUKKKK

@app.route("/stok_masuk", methods=["GET","POST"])
def stok_masuk():

    if "id" not in session or session["role"] != "karyawan":
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":

        bahan = request.form["bahan_id"]
        supplier = request.form["supplier_id"]   # <-- tambah ini
        jumlah = int(request.form["jumlah"])
        tanggal = request.form["tanggal"]
        ket = request.form["keterangan"]

        cur.execute("""
        INSERT INTO stok_masuk
        (bahan_id,supplier_id,jumlah,tanggal,karyawan_id,keterangan)
        VALUES(%s,%s,%s,%s,%s,%s)
        """,(
            bahan,
            supplier,
            jumlah,
            tanggal,
            session["id"],
            ket
        ))

        cur.execute("""
        UPDATE bahan_baku
        SET stok = stok + %s
        WHERE id = %s
        """,(jumlah,bahan))

        conn.commit()

        return redirect("/stok_masuk")

    # ==========================
    # DATA BAHAN
    # ==========================
    cur.execute("""
    SELECT id,nama_bahan
    FROM bahan_baku
    ORDER BY nama_bahan
    """)

    bahan = cur.fetchall()

    # ==========================
    # DATA SUPPLIER
    # ==========================
    cur.execute("""
    SELECT id,nama_supplier
    FROM supplier
    ORDER BY nama_supplier
    """)

    supplier = cur.fetchall()

    # ==========================
    # DATA TABEL
    # ==========================
    cur.execute("""
    SELECT

        sm.id,
        bb.nama_bahan,
        s.nama_supplier,
        sm.jumlah,
        sm.tanggal,
        sm.keterangan

    FROM stok_masuk sm

    JOIN bahan_baku bb
        ON bb.id = sm.bahan_id

    JOIN supplier s
        ON s.id = sm.supplier_id

    ORDER BY sm.id DESC
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "karyawan/stok_masuk.html",
        bahan=bahan,
        supplier=supplier,
        data=data
    )

## STOK KELUARRR
@app.route("/stok_keluar", methods=["GET","POST"])
def stok_keluar():

    if "id" not in session or session["role"]!="karyawan":
        return redirect("/")

    conn=get_connection()
    cur=conn.cursor()

    if request.method=="POST":

        bahan=request.form["bahan_id"]
        jumlah=int(request.form["jumlah"])
        tanggal=request.form["tanggal"]
        ket=request.form["keterangan"]

        cur.execute("""
        INSERT INTO stok_keluar
        (bahan_id,jumlah,tanggal,karyawan_id,keterangan)
        VALUES(%s,%s,%s,%s,%s)
        """,(bahan,jumlah,tanggal,session["id"],ket))

        cur.execute("""
        UPDATE bahan_baku
        SET stok=stok-%s
        WHERE id=%s
        """,(jumlah,bahan))

        conn.commit()

        return redirect("/stok_keluar")

    cur.execute("""
    SELECT id,nama_bahan
    FROM bahan_baku
    ORDER BY nama_bahan
    """)

    bahan=cur.fetchall()

    cur.execute("""
    SELECT

    sk.id,
    bb.nama_bahan,
    sk.jumlah,
    sk.tanggal,
    sk.keterangan

    FROM stok_keluar sk

    JOIN bahan_baku bb
    ON bb.id=sk.bahan_id

    ORDER BY sk.id DESC
    """)

    data=cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "karyawan/stok_keluar.html",
        bahan=bahan,
        data=data
    )

## LAPORANNNN
@app.route("/laporan")
def laporan():

    if "id" not in session:
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""

    SELECT

    bb.nama_bahan,

    bb.satuan,

    bb.stok,

    bb.stok_minimum,

    COALESCE(m.total_masuk,0),

    COALESCE(k.total_keluar,0)

    FROM bahan_baku bb

    LEFT JOIN

    (

        SELECT

        bahan_id,

        SUM(jumlah) total_masuk

        FROM stok_masuk

        GROUP BY bahan_id

    ) m

    ON bb.id=m.bahan_id

    LEFT JOIN

    (

        SELECT

        bahan_id,

        SUM(jumlah) total_keluar

        FROM stok_keluar

        GROUP BY bahan_id

    ) k

    ON bb.id=k.bahan_id

    ORDER BY bb.nama_bahan

    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "owner/laporan.html",
        data=data
    )

## DOWNLOAD LAPORANNNN

@app.route("/download_laporan")
def download_laporan():

    if "id" not in session or session["role"] != "owner":
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            nama_bahan,
            satuan,
            stok,
            stok_minimum,

            COALESCE((
                SELECT SUM(jumlah)
                FROM stok_masuk
                WHERE bahan_id=bahan_baku.id
            ),0) AS masuk,

            COALESCE((
                SELECT SUM(jumlah)
                FROM stok_keluar
                WHERE bahan_id=bahan_baku.id
            ),0) AS keluar,

            CASE
                WHEN stok<=stok_minimum
                THEN 'Minimum'
                ELSE 'Aman'
            END

        FROM bahan_baku

        ORDER BY nama_bahan
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    wb = Workbook()

    ws = wb.active

    ws.title = "Laporan Stok"

    header = [
        "No",
        "Nama Bahan",
        "Satuan",
        "Stok",
        "Minimum",
        "Stok Masuk",
        "Stok Keluar",
        "Status"
    ]

    for col, value in enumerate(header, start=1):
        cell = ws.cell(row=1, column=col)
        cell.value = value
        cell.font = Font(bold=True)

    no = 1

    for row in data:

        ws.append([
            no,
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6]
        ])

        no += 1

    output = io.BytesIO()

    wb.save(output)

    output.seek(0)

    return send_file(
        output,
        download_name="Laporan_Stok_DKriuk.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    app.run(debug=True)
