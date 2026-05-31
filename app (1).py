"""
Created on Thu May  7 18:49:12 2026

@author: Asus
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import pandas as pd
import plotly.graph_objects as go

from classes.provider import Provider
from classes.datacenter import Datacenter
from classes.serverspec import ServerSpec
from classes.server import Server
from classes.usagequota import UsageQuota
from classes.userlogin import Userlogin

app = Flask(__name__)
app.secret_key = 'cloud_secret_key_2026'

DB_PATH = 'data/cloud.db'

Provider.read(DB_PATH)
Datacenter.read(DB_PATH)
ServerSpec.read(DB_PATH)
Server.read(DB_PATH)
UsageQuota.read(DB_PATH)
Userlogin.read(DB_PATH)

def logged_in():
    return session.get('user') is not None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if logged_in():
        return redirect(url_for('index'))
    return render_template('login.html', user='', resul='')

@app.route('/chklogin', methods=['POST'])
def chklogin():
    user = request.form['user']
    password = request.form['password']
    result = Userlogin.chk_password(user, password)
    if result == 'Valid':
        session['user'] = user
        return redirect(url_for('index'))
    return render_template('login.html', user=user, resul=result)

@app.route('/logoff')
def logoff():
    session.pop('user', None)
    return redirect(url_for('login'))

prev_option = ''

@app.route('/userlogin', methods=['GET', 'POST'])
def userlogin():
    global prev_option
    if not logged_in():
        return redirect(url_for('login'))
    msg = ''
    ulogin = session.get('user')
    user_id = Userlogin.get_user_id(ulogin)
    group = Userlogin.obj[user_id].usergroup
    if group != 'admin':
        Userlogin.current(user_id)
    mode = 'show'
    option = request.args.get('option')
    if option == 'edit':
        mode = 'edit'
    elif option == 'insert':
        mode = 'insert'
    elif option == 'delete':
        obj = Userlogin.current()
        if obj.id != user_id:
            Userlogin.remove(obj.id)
            if not Userlogin.previous():
                Userlogin.first()
        else:
            msg = 'Não podes eliminar o teu próprio utilizador'
    elif prev_option == 'insert' and option == 'save':
        user = request.form['user']
        if len(Userlogin.find(user, 'user')) == 0:
            obj = Userlogin(0, user, request.form['usergroup'],
                            Userlogin.set_password(request.form['password']))
            Userlogin.insert(obj.id)
            Userlogin.last()
        else:
            msg = 'Nome de utilizador já existe'
            mode = 'insert'
    elif prev_option == 'edit' and option == 'save':
        obj = Userlogin.current()
        if group == 'admin':
            obj.usergroup = request.form['usergroup']
        if request.form['password'] != '':
            obj.password = Userlogin.set_password(request.form['password'])
        Userlogin.update(obj.id)
    elif option == 'first':
        Userlogin.first()
    elif option == 'previous':
        Userlogin.previous()
    elif option == 'next':
        Userlogin.nextrec()
    elif option == 'last':
        Userlogin.last()
    elif option == 'exit':
        return redirect(url_for('index'))
    prev_option = option
    obj = Userlogin.current()
    if mode == 'insert' or len(Userlogin.lst) == 0:
        id, user, usergroup = 0, '', ''
    else:
        id = obj.id
        user = obj.user
        usergroup = obj.usergroup
    return render_template('userlogin.html', mode=mode, msg=msg,
                           id=id, user=user, usergroup=usergroup, group=group)

@app.route('/')
def index():
    if not logged_in():
        return redirect(url_for('login'))
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT COALESCE(SUM(cost),0), COALESCE(AVG(cost),0), COUNT(*) FROM UsageQuota")
    total_cost, avg_cost, total_quotas = cur.fetchone()
    cur.execute("""SELECT p.name, SUM(u.cost) as t FROM UsageQuota u
                   JOIN Provider p ON u.provider_id=p.id
                   GROUP BY p.id ORDER BY t DESC LIMIT 1""")
    r = cur.fetchone()
    top_provider, top_provider_cost = (r[0], r[1]) if r else ('—', 0)
    cur.execute("""SELECT d.title, COUNT(*) as c FROM UsageQuota u
                   JOIN Datacenter d ON u.datacenter_id=d.id
                   GROUP BY d.id ORDER BY c DESC LIMIT 1""")
    r = cur.fetchone()
    top_dc, top_dc_count = (r[0], r[1]) if r else ('—', 0)
    cur.execute("""SELECT p.name, COUNT(*) as c FROM Server s
                   JOIN Provider p ON s.provider_id=p.id
                   GROUP BY p.id ORDER BY c DESC LIMIT 1""")
    r = cur.fetchone()
    top_server_provider, top_server_count = (r[0], r[1]) if r else ('—', 0)
    cur.execute("""SELECT substr(usage_date,1,4) as y, SUM(cost) as t
                   FROM UsageQuota GROUP BY y ORDER BY t DESC LIMIT 1""")
    r = cur.fetchone()
    top_year, top_year_cost = (r[0], r[1]) if r else ('—', 0)
    cur.execute("""SELECT ss.ram_gb || 'GB/' || ss.cpu_cores || ' cores', COUNT(*) as c
                   FROM Server s JOIN ServerSpec ss ON s.spec_id=ss.id
                   GROUP BY s.spec_id ORDER BY c DESC LIMIT 1""")
    r = cur.fetchone()
    top_spec, top_spec_count = (r[0], r[1]) if r else ('—', 0)
    cur.execute("SELECT COALESCE(MAX(cost),0), COALESCE(MIN(cost),0) FROM UsageQuota")
    max_cost, min_cost = cur.fetchone()
    con.close()
    stats = dict(total_cost=total_cost, avg_cost=avg_cost, total_quotas=total_quotas,
                 top_provider=top_provider, top_provider_cost=top_provider_cost,
                 top_dc=top_dc, top_dc_count=top_dc_count,
                 top_server_provider=top_server_provider, top_server_count=top_server_count,
                 top_year=top_year, top_year_cost=top_year_cost,
                 top_spec=top_spec, top_spec_count=top_spec_count,
                 max_cost=max_cost, min_cost=min_cost)
    return render_template('index.html', stats=stats)

@app.route('/charts')
def charts():
    if not logged_in():
        return redirect(url_for('login'))
    return render_template('charts.html',
                           chart_above_avg=get_chart_above_avg(),
                           chart_top_dc=get_chart_top_dc(),
                           chart_servers=get_chart_servers(),
                           chart_yearly=get_chart_yearly())

@app.route('/providers')
def providers():
    if not logged_in():
        return redirect(url_for('login'))
    search = request.args.get('search', '')
    sort = request.args.get('sort', '')
    order = request.args.get('order', 'asc')
    page = int(request.args.get('page', 1))
    items = [Provider.obj[k] for k in Provider.lst]
    if search:
        items = [p for p in items if search.lower() in p.name.lower()]
    if sort in ['name', 'creation_date']:
        items.sort(key=lambda x: str(getattr(x, sort)), reverse=(order == 'desc'))
    total = len(items)
    per_page = 50
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    items = items[(page-1)*per_page : page*per_page]
    return render_template('list.html', items=items, cls='Provider',
                           des=Provider.des, att=Provider.att,
                           search=search, sort=sort, order=order,
                           page=page, total=total, total_pages=total_pages, zip=zip)

@app.route('/providers/<int:id>')
def provider_detail(id):
    if not logged_in():
        return redirect(url_for('login'))
    obj = Provider.obj.get(id)
    if not obj:
        flash('Provider não encontrado.', 'error')
        return redirect(url_for('providers'))
    servers = [Server.obj[k] for k in Server.lst if Server.obj[k].provider_id == id]
    quotas  = [UsageQuota.obj[k] for k in UsageQuota.lst if UsageQuota.obj[k].provider_id == id]
    specs_map = {k: f"{ServerSpec.obj[k].ram_gb}GB/{ServerSpec.obj[k].cpu_cores}c" for k in ServerSpec.lst}
    dcs_map   = {k: Datacenter.obj[k].title for k in Datacenter.lst}
    total_cost = sum(q.cost for q in quotas)
    fields = [('Id', f'#{obj.id}'), ('Nome', obj.name), ('Data de Criação', obj.creation_date)]
    stats  = [('Nº de Servidores', len(servers)), ('Nº de Quotas', len(quotas)), ('Custo Total', f'€{total_cost:,.2f}')]
    server_rows = [{'cells': [
        {'text': f'#{s.id}', 'url': None, 'badge': None, 'btn_url': None, 'btn_type': None},
        {'text': s.extra_info, 'url': None, 'badge': None, 'btn_url': None, 'btn_type': None},
        {'text': f'#{s.spec_id} {specs_map.get(s.spec_id,"?")}', 'url': url_for('serverspec_detail', id=s.spec_id), 'badge': 'badge-green', 'btn_url': None, 'btn_type': None},
        {'text': 'Ver', 'url': None, 'badge': None, 'btn_url': url_for('server_detail', id=s.id), 'btn_type': 'success'},
    ]} for s in servers]
    quota_rows = [{'cells': [
        {'text': f'#{q.id}', 'url': None, 'badge': None, 'btn_url': None, 'btn_type': None},
        {'text': f'#{q.datacenter_id} {dcs_map.get(q.datacenter_id,"?")}', 'url': url_for('datacenter_detail', id=q.datacenter_id), 'badge': 'badge-purple', 'btn_url': None, 'btn_type': None},
        {'text': str(q.usage_date), 'url': None, 'badge': None, 'btn_url': None, 'btn_type': None},
        {'text': f'€{q.cost:,.2f}', 'url': None, 'badge': None, 'btn_url': None, 'btn_type': None},
        {'text': 'Editar', 'url': None, 'badge': None, 'btn_url': url_for('usagequota_edit', id=q.id), 'btn_type': 'secondary'},
    ]} for q in quotas]
    related = [
        {'title': '🖥️ Servidores', 'headers': ['Id','Info Extra','Spec',''], 'rows': server_rows},
        {'title': '📊 Quotas', 'headers': ['Id','Datacenter','Data','Custo',''], 'rows': quota_rows},
    ]
    return render_template('detail.html', cls='Provider', obj=obj, obj_title=obj.name,
                           fields=fields, stats=stats, related_tables=related,
                           back_url=url_for('providers'),
                           edit_url=url_for('provider_edit', id=id),
                           delete_url=url_for('provider_delete', id=id))

@app.route('/providers/new', methods=['GET', 'POST'])
def provider_new():
    if not logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            Provider(0, request.form['name'], request.form['creation_date'])
            Provider.insert(max(Provider.lst))
            flash('Provider criado!', 'success')
            return redirect(url_for('providers'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    return render_template('form.html', cls='Provider', obj=None,
                           fields=[('name','Nome','text'),('creation_date','Data de Criação','date')])

@app.route('/providers/<int:id>/edit', methods=['GET', 'POST'])
def provider_edit(id):
    if not logged_in():
        return redirect(url_for('login'))
    obj = Provider.obj.get(id)
    if not obj:
        flash('Provider não encontrado.', 'error')
        return redirect(url_for('providers'))
    if request.method == 'POST':
        try:
            obj.name = request.form['name']
            obj.creation_date = request.form['creation_date']
            Provider.update(id)
            flash('Provider atualizado!', 'success')
            return redirect(url_for('provider_detail', id=id))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    fields = [('name','Nome','text'),('creation_date','Data de Criação','date')]
    values = {'name': obj.name, 'creation_date': obj.creation_date}
    return render_template('form.html', cls='Provider', obj=obj, fields=fields, values=values)

@app.route('/providers/<int:id>/delete', methods=['POST'])
def provider_delete(id):
    if not logged_in():
        return redirect(url_for('login'))
    try:
        Provider.remove(id)
        flash('Provider eliminado.', 'success')
    except Exception as e:
        flash(f'Erro: {e}', 'error')
    return redirect(url_for('providers'))

@app.route('/datacenters')
def datacenters():
    if not logged_in():
        return redirect(url_for('login'))
    search = request.args.get('search', '')
    sort = request.args.get('sort', '')
    order = request.args.get('order', 'asc')
    page = int(request.args.get('page', 1))
    items = [Datacenter.obj[k] for k in Datacenter.lst]
    if search:
        items = [d for d in items if search.lower() in d.title.lower()]
    if sort in ['title', 'category']:
        items.sort(key=lambda x: str(getattr(x, sort)), reverse=(order == 'desc'))
    total = len(items)
    per_page = 50
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    items = items[(page-1)*per_page : page*per_page]
    return render_template('list.html', items=items, cls='Datacenter',
                           des=Datacenter.des, att=Datacenter.att,
                           search=search, sort=sort, order=order,
                           page=page, total=total, total_pages=total_pages, zip=zip)

@app.route('/datacenters/<int:id>')
def datacenter_detail(id):
    if not logged_in():
        return redirect(url_for('login'))
    obj = Datacenter.obj.get(id)
    if not obj:
        flash('Datacenter não encontrado.', 'error')
        return redirect(url_for('datacenters'))
    quotas = [UsageQuota.obj[k] for k in UsageQuota.lst if UsageQuota.obj[k].datacenter_id == id]
    providers_map = {k: Provider.obj[k].name for k in Provider.lst}
    total_cost = sum(q.cost for q in quotas)
    avg_cost   = total_cost / len(quotas) if quotas else 0
    fields = [('Id', f'#{obj.id}'), ('Nome', obj.title), ('Categoria', obj.category)]
    stats  = [('Nº de Quotas', len(quotas)), ('Custo Total', f'€{total_cost:,.2f}'), ('Custo Médio', f'€{avg_cost:,.2f}')]
    quota_rows = [{'cells': [
        {'text': f'#{q.id}', 'url': None, 'badge': None, 'btn_url': None, 'btn_type': None},
        {'text': f'#{q.provider_id} {providers_map.get(q.provider_id,"?")}', 'url': url_for('provider_detail', id=q.provider_id), 'badge': 'badge-blue', 'btn_url': None, 'btn_type': None},
        {'text': str(q.usage_date), 'url': None, 'badge': None, 'btn_url': None, 'btn_type': None},
        {'text': f'€{q.cost:,.2f}', 'url': None, 'badge': None, 'btn_url': None, 'btn_type': None},
        {'text': 'Editar', 'url': None, 'badge': None, 'btn_url': url_for('usagequota_edit', id=q.id), 'btn_type': 'secondary'},
    ]} for q in quotas]
    related = [{'title': '📊 Quotas de Utilização', 'headers': ['Id','Provider','Data','Custo',''], 'rows': quota_rows}]
    return render_template('detail.html', cls='Datacenter', obj=obj, obj_title=obj.title,
                           fields=fields, stats=stats, related_tables=related,
                           back_url=url_for('datacenters'),
                           edit_url=url_for('datacenter_edit', id=id),
                           delete_url=url_for('datacenter_delete', id=id))

@app.route('/datacenters/new', methods=['GET', 'POST'])
def datacenter_new():
    if not logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            Datacenter(0, request.form['title'], request.form['category'])
            Datacenter.insert(max(Datacenter.lst))
            flash('Datacenter criado!', 'success')
            return redirect(url_for('datacenters'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    return render_template('form.html', cls='Datacenter', obj=None,
                           fields=[('title','Nome','text'),('category','Categoria','text')])

@app.route('/datacenters/<int:id>/edit', methods=['GET', 'POST'])
def datacenter_edit(id):
    if not logged_in():
        return redirect(url_for('login'))
    obj = Datacenter.obj.get(id)
    if not obj:
        flash('Datacenter não encontrado.', 'error')
        return redirect(url_for('datacenters'))
    if request.method == 'POST':
        try:
            obj.title = request.form['title']
            obj.category = request.form['category']
            Datacenter.update(id)
            flash('Datacenter atualizado!', 'success')
            return redirect(url_for('datacenter_detail', id=id))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    fields = [('title','Nome','text'),('category','Categoria','text')]
    values = {'title': obj.title, 'category': obj.category}
    return render_template('form.html', cls='Datacenter', obj=obj, fields=fields, values=values)

@app.route('/datacenters/<int:id>/delete', methods=['POST'])
def datacenter_delete(id):
    if not logged_in():
        return redirect(url_for('login'))
    try:
        Datacenter.remove(id)
        flash('Datacenter eliminado.', 'success')
    except Exception as e:
        flash(f'Erro: {e}', 'error')
    return redirect(url_for('datacenters'))

@app.route('/serverspecs')
def serverspecs():
    if not logged_in():
        return redirect(url_for('login'))
    search = request.args.get('search', '')
    sort = request.args.get('sort', '')
    order = request.args.get('order', 'asc')
    page = int(request.args.get('page', 1))
    items = [ServerSpec.obj[k] for k in ServerSpec.lst]
    if search:
        items = [s for s in items if search.lower() in s.operating_system.lower()]
    if sort in ['ram_gb', 'cpu_cores', 'operating_system', 'storage_gb']:
        items.sort(key=lambda x: getattr(x, sort), reverse=(order == 'desc'))
    total = len(items)
    per_page = 50
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    items = items[(page-1)*per_page : page*per_page]
    return render_template('list.html', items=items, cls='ServerSpec',
                           des=ServerSpec.des, att=ServerSpec.att,
                           search=search, sort=sort, order=order,
                           page=page, total=total, total_pages=total_pages, zip=zip)

@app.route('/serverspecs/<int:id>')
def serverspec_detail(id):
    if not logged_in():
        return redirect(url_for('login'))
    obj = ServerSpec.obj.get(id)
    if not obj:
        flash('ServerSpec não encontrado.', 'error')
        return redirect(url_for('serverspecs'))
    servers = [Server.obj[k] for k in Server.lst if Server.obj[k].spec_id == id]
    providers_map = {k: Provider.obj[k].name for k in Provider.lst}
    fields = [('Id', f'#{obj.id}'), ('RAM', f'{obj.ram_gb} GB'), ('Núcleos CPU', obj.cpu_cores),
              ('Sistema Operativo', obj.operating_system), ('Armazenamento', f'{obj.storage_gb} GB')]
    stats  = [('Servidores com esta Spec', len(servers))]
    server_rows = [{'cells': [
        {'text': f'#{s.id}', 'url': None, 'badge': None, 'btn_url': None, 'btn_type': None},
        {'text': s.extra_info, 'url': None, 'badge': None, 'btn_url': None, 'btn_type': None},
        {'text': f'#{s.provider_id} {providers_map.get(s.provider_id,"?")}', 'url': url_for('provider_detail', id=s.provider_id), 'badge': 'badge-blue', 'btn_url': None, 'btn_type': None},
        {'text': 'Ver', 'url': None, 'badge': None, 'btn_url': url_for('server_detail', id=s.id), 'btn_type': 'success'},
    ]} for s in servers]
    related = [{'title': '🖥️ Servidores com esta Especificação', 'headers': ['Id','Info Extra','Provider',''], 'rows': server_rows}]
    return render_template('detail.html', cls='ServerSpec', obj=obj, obj_title=f'#{obj.id}',
                           fields=fields, stats=stats, related_tables=related,
                           back_url=url_for('serverspecs'),
                           edit_url=url_for('serverspec_edit', id=id),
                           delete_url=url_for('serverspec_delete', id=id))

@app.route('/serverspecs/new', methods=['GET', 'POST'])
def serverspec_new():
    if not logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            ServerSpec(0, request.form['ram_gb'], request.form['cpu_cores'],
                       request.form['operating_system'], request.form['storage_gb'])
            ServerSpec.insert(max(ServerSpec.lst))
            flash('ServerSpec criado!', 'success')
            return redirect(url_for('serverspecs'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    fields = [('ram_gb','RAM (GB)','number'),('cpu_cores','Núcleos CPU','number'),
              ('operating_system','Sistema Operativo','text'),('storage_gb','Armazenamento (GB)','number')]
    return render_template('form.html', cls='ServerSpec', obj=None, fields=fields)

@app.route('/serverspecs/<int:id>/edit', methods=['GET', 'POST'])
def serverspec_edit(id):
    if not logged_in():
        return redirect(url_for('login'))
    obj = ServerSpec.obj.get(id)
    if not obj:
        flash('ServerSpec não encontrado.', 'error')
        return redirect(url_for('serverspecs'))
    if request.method == 'POST':
        try:
            obj.ram_gb = request.form['ram_gb']
            obj.cpu_cores = request.form['cpu_cores']
            obj.operating_system = request.form['operating_system']
            obj.storage_gb = request.form['storage_gb']
            ServerSpec.update(id)
            flash('ServerSpec atualizado!', 'success')
            return redirect(url_for('serverspec_detail', id=id))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    fields = [('ram_gb','RAM (GB)','number'),('cpu_cores','Núcleos CPU','number'),
              ('operating_system','Sistema Operativo','text'),('storage_gb','Armazenamento (GB)','number')]
    values = {'ram_gb': obj.ram_gb, 'cpu_cores': obj.cpu_cores,
              'operating_system': obj.operating_system, 'storage_gb': obj.storage_gb}
    return render_template('form.html', cls='ServerSpec', obj=obj, fields=fields, values=values)

@app.route('/serverspecs/<int:id>/delete', methods=['POST'])
def serverspec_delete(id):
    if not logged_in():
        return redirect(url_for('login'))
    try:
        ServerSpec.remove(id)
        flash('ServerSpec eliminado.', 'success')
    except Exception as e:
        flash(f'Erro: {e}', 'error')
    return redirect(url_for('serverspecs'))

@app.route('/servers')
def servers():
    if not logged_in():
        return redirect(url_for('login'))
    search = request.args.get('search', '')
    sort = request.args.get('sort', '')
    order = request.args.get('order', 'asc')
    page = int(request.args.get('page', 1))
    items = [Server.obj[k] for k in Server.lst]
    if search:
        items = [s for s in items if search.lower() in s.extra_info.lower()]
    if sort in ['extra_info', 'provider_id', 'spec_id']:
        items.sort(key=lambda x: getattr(x, sort), reverse=(order == 'desc'))
    total = len(items)
    per_page = 50
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    items = items[(page-1)*per_page : page*per_page]
    providers_map = {k: Provider.obj[k].name for k in Provider.lst}
    specs_map = {k: f"{ServerSpec.obj[k].ram_gb}GB/{ServerSpec.obj[k].cpu_cores}c" for k in ServerSpec.lst}
    return render_template('list.html', items=items, cls='Server',
                           des=Server.des, att=Server.att,
                           providers_map=providers_map, specs_map=specs_map,
                           search=search, sort=sort, order=order,
                           page=page, total=total, total_pages=total_pages, zip=zip)

@app.route('/servers/<int:id>')
def server_detail(id):
    if not logged_in():
        return redirect(url_for('login'))
    obj = Server.obj.get(id)
    if not obj:
        flash('Server não encontrado.', 'error')
        return redirect(url_for('servers'))
    provider = Provider.obj.get(obj.provider_id)
    spec     = ServerSpec.obj.get(obj.spec_id)
    fields = [('Id', f'#{obj.id}'), ('Info Extra', obj.extra_info),
              ('Provider', f'#{provider.id} {provider.name}'),
              ('ServerSpec', f'#{spec.id} {spec.ram_gb}GB/{spec.cpu_cores} cores/{spec.operating_system}')]
    stats  = [('RAM', f'{spec.ram_gb} GB'), ('CPU Cores', spec.cpu_cores),
              ('Sistema Operativo', spec.operating_system), ('Armazenamento', f'{spec.storage_gb} GB')]
    return render_template('detail.html', cls='Server', obj=obj, obj_title=f'#{obj.id}',
                           fields=fields, stats=stats, related_tables=[],
                           back_url=url_for('servers'),
                           edit_url=url_for('server_edit', id=id),
                           delete_url=url_for('server_delete', id=id))

@app.route('/servers/new', methods=['GET', 'POST'])
def server_new():
    if not logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            Server(0, request.form['extra_info'],
                   int(request.form['provider_id']), int(request.form['spec_id']))
            Server.insert(max(Server.lst))
            flash('Server criado!', 'success')
            return redirect(url_for('servers'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    providers = [Provider.obj[k] for k in Provider.lst]
    specs     = [ServerSpec.obj[k] for k in ServerSpec.lst]
    return render_template('form_server.html', cls='Server', obj=None,
                           providers=providers, specs=specs)

@app.route('/servers/<int:id>/edit', methods=['GET', 'POST'])
def server_edit(id):
    if not logged_in():
        return redirect(url_for('login'))
    obj = Server.obj.get(id)
    if not obj:
        flash('Server não encontrado.', 'error')
        return redirect(url_for('servers'))
    if request.method == 'POST':
        try:
            obj.extra_info  = request.form['extra_info']
            obj.provider_id = int(request.form['provider_id'])
            obj.spec_id     = int(request.form['spec_id'])
            Server.update(id)
            flash('Server atualizado!', 'success')
            return redirect(url_for('server_detail', id=id))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    providers = [Provider.obj[k] for k in Provider.lst]
    specs     = [ServerSpec.obj[k] for k in ServerSpec.lst]
    return render_template('form_server.html', cls='Server', obj=obj,
                           providers=providers, specs=specs)

@app.route('/servers/<int:id>/delete', methods=['POST'])
def server_delete(id):
    if not logged_in():
        return redirect(url_for('login'))
    try:
        Server.remove(id)
        flash('Server eliminado.', 'success')
    except Exception as e:
        flash(f'Erro: {e}', 'error')
    return redirect(url_for('servers'))

@app.route('/usagequotas')
def usagequotas():
    if not logged_in():
        return redirect(url_for('login'))
    sort = request.args.get('sort', '')
    order = request.args.get('order', 'asc')
    page = int(request.args.get('page', 1))
    items = [UsageQuota.obj[k] for k in UsageQuota.lst]
    if sort in ['provider_id', 'datacenter_id', 'usage_date', 'cost']:
        items.sort(key=lambda x: getattr(x, sort), reverse=(order == 'desc'))
    total = len(items)
    per_page = 50
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    items = items[(page-1)*per_page : page*per_page]
    providers_map   = {k: Provider.obj[k].name for k in Provider.lst}
    datacenters_map = {k: Datacenter.obj[k].title for k in Datacenter.lst}
    return render_template('list.html', items=items, cls='UsageQuota',
                           des=UsageQuota.des, att=UsageQuota.att,
                           providers_map=providers_map, datacenters_map=datacenters_map,
                           search='', sort=sort, order=order,
                           page=page, total=total, total_pages=total_pages, zip=zip)

@app.route('/usagequotas/new', methods=['GET', 'POST'])
def usagequota_new():
    if not logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            UsageQuota(0, int(request.form['provider_id']),
                       int(request.form['datacenter_id']),
                       request.form['usage_date'], float(request.form['cost']))
            UsageQuota.insert(max(UsageQuota.lst))
            flash('UsageQuota criada!', 'success')
            return redirect(url_for('usagequotas'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    providers   = [Provider.obj[k] for k in Provider.lst]
    datacenters = [Datacenter.obj[k] for k in Datacenter.lst]
    return render_template('form_usagequota.html', cls='UsageQuota', obj=None,
                           providers=providers, datacenters=datacenters)

@app.route('/usagequotas/<int:id>/edit', methods=['GET', 'POST'])
def usagequota_edit(id):
    if not logged_in():
        return redirect(url_for('login'))
    obj = UsageQuota.obj.get(id)
    if not obj:
        flash('UsageQuota não encontrada.', 'error')
        return redirect(url_for('usagequotas'))
    if request.method == 'POST':
        try:
            obj.provider_id   = int(request.form['provider_id'])
            obj.datacenter_id = int(request.form['datacenter_id'])
            obj.usage_date    = request.form['usage_date']
            obj.cost          = float(request.form['cost'])
            UsageQuota.update(id)
            flash('UsageQuota atualizada!', 'success')
            return redirect(url_for('usagequotas'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    providers   = [Provider.obj[k] for k in Provider.lst]
    datacenters = [Datacenter.obj[k] for k in Datacenter.lst]
    return render_template('form_usagequota.html', cls='UsageQuota', obj=obj,
                           providers=providers, datacenters=datacenters)

@app.route('/usagequotas/<int:id>/delete', methods=['POST'])
def usagequota_delete(id):
    if not logged_in():
        return redirect(url_for('login'))
    try:
        UsageQuota.remove(id)
        flash('UsageQuota eliminada.', 'success')
    except Exception as e:
        flash(f'Erro: {e}', 'error')
    return redirect(url_for('usagequotas'))

def get_chart_above_avg():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT p.name as provider, SUM(u.cost) as total
        FROM UsageQuota u JOIN Provider p ON u.provider_id = p.id
        GROUP BY p.id, p.name ORDER BY total DESC
    """, con)
    con.close()
    media = df['total'].mean()
    df = df[df['total'] > media].head(20).sort_values('total')
    fig = go.Figure(go.Bar(
        x=df['total'], y=df['provider'], orientation='h',
        marker_color='#3498db',
        hovertemplate='<b>%{y}</b><br>€%{x:,.0f}<extra></extra>',
    ))
    fig.add_vline(x=media, line_dash='dash', line_color='red',
                  annotation_text=f'Média: €{media:,.0f}')
    fig.update_layout(height=450, margin=dict(l=10,r=10,t=10,b=10),
                      xaxis_title='Custo Total (€)', showlegend=False,
                      plot_bgcolor='white', paper_bgcolor='white')
    return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

def get_chart_top_dc():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT d.title as datacenter, COUNT(*) as total
        FROM UsageQuota u JOIN Datacenter d ON u.datacenter_id = d.id
        GROUP BY d.id, d.title ORDER BY total DESC LIMIT 10
    """, con)
    con.close()
    df = df.sort_values('total')
    fig = go.Figure(go.Bar(
        x=df['total'], y=df['datacenter'], orientation='h',
        marker_color='#9b59b6',
        hovertemplate='<b>%{y}</b><br>%{x} quotas<extra></extra>',
    ))
    fig.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10),
                      xaxis_title='Nº de Quotas', showlegend=False,
                      plot_bgcolor='white', paper_bgcolor='white')
    return fig.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})

def get_chart_servers():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT p.name as provider, COUNT(*) as servidores
        FROM Server s JOIN Provider p ON s.provider_id = p.id
        GROUP BY p.id, p.name ORDER BY servidores DESC LIMIT 10
    """, con)
    con.close()
    df = df.sort_values('servidores')
    fig = go.Figure(go.Bar(
        x=df['servidores'], y=df['provider'], orientation='h',
        marker_color='#2ecc71',
        hovertemplate='<b>%{y}</b><br>%{x} servidores<extra></extra>',
    ))
    fig.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10),
                      xaxis_title='Nº de Servidores', showlegend=False,
                      plot_bgcolor='white', paper_bgcolor='white')
    return fig.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})

def get_chart_yearly():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT substr(usage_date,1,4) as ano,
               SUM(cost) as total, AVG(cost) as media
        FROM UsageQuota GROUP BY ano ORDER BY ano
    """, con)
    con.close()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['ano'], y=df['total'], name='Total (€)',
                         marker_color='#3498db',
                         hovertemplate='%{x}: €%{y:,.0f}<extra></extra>'))
    fig.add_trace(go.Scatter(x=df['ano'], y=df['media'], name='Média (€)',
                             mode='lines+markers', line=dict(color='red', width=2),
                             hovertemplate='%{x}: €%{y:,.0f}<extra></extra>',
                             yaxis='y2'))
    fig.update_layout(height=350, margin=dict(l=10,r=10,t=10,b=10),
                      xaxis_title='Ano',
                      yaxis=dict(title='Total (€)'),
                      yaxis2=dict(title='Média (€)', overlaying='y', side='right'),
                      plot_bgcolor='white', paper_bgcolor='white')
    return fig.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})


@app.route('/change_password', methods=['POST'])
def change_password():
    if not logged_in():
        return redirect(url_for('login'))
    current = request.form['current_password']
    new = request.form['new_password']
    confirm = request.form['confirm_password']
    user = session.get('user')
    result = Userlogin.chk_password(user, current)
    if result != 'Valid':
        pw_error = 'Password atual incorreta.'
    elif new != confirm:
        pw_error = 'As passwords novas não coincidem.'
    elif len(new) < 4:
        pw_error = 'A nova password deve ter pelo menos 4 caracteres.'
    else:
        user_id = Userlogin.get_user_id(user)
        obj = Userlogin.obj[user_id]
        obj.password = Userlogin.set_password(new)
        Userlogin.update(user_id)
        flash('Password alterada com sucesso!', 'success')
        return redirect(url_for('index'))
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT COALESCE(SUM(cost),0), COALESCE(AVG(cost),0), COUNT(*) FROM UsageQuota")
    total_cost, avg_cost, total_quotas = cur.fetchone()
    cur.execute("SELECT p.name, SUM(u.cost) as t FROM UsageQuota u JOIN Provider p ON u.provider_id=p.id GROUP BY p.id ORDER BY t DESC LIMIT 1")
    r = cur.fetchone()
    top_provider, top_provider_cost = (r[0], r[1]) if r else ('—', 0)
    cur.execute("SELECT d.title, COUNT(*) as c FROM UsageQuota u JOIN Datacenter d ON u.datacenter_id=d.id GROUP BY d.id ORDER BY c DESC LIMIT 1")
    r = cur.fetchone()
    top_dc, top_dc_count = (r[0], r[1]) if r else ('—', 0)
    cur.execute("SELECT p.name, COUNT(*) as c FROM Server s JOIN Provider p ON s.provider_id=p.id GROUP BY p.id ORDER BY c DESC LIMIT 1")
    r = cur.fetchone()
    top_server_provider, top_server_count = (r[0], r[1]) if r else ('—', 0)
    cur.execute("SELECT substr(usage_date,1,4) as y, SUM(cost) as t FROM UsageQuota GROUP BY y ORDER BY t DESC LIMIT 1")
    r = cur.fetchone()
    top_year, top_year_cost = (r[0], r[1]) if r else ('—', 0)
    cur.execute("SELECT ss.ram_gb || 'GB/' || ss.cpu_cores || ' cores', COUNT(*) as c FROM Server s JOIN ServerSpec ss ON s.spec_id=ss.id GROUP BY s.spec_id ORDER BY c DESC LIMIT 1")
    r = cur.fetchone()
    top_spec, top_spec_count = (r[0], r[1]) if r else ('—', 0)
    cur.execute("SELECT COALESCE(MAX(cost),0), COALESCE(MIN(cost),0) FROM UsageQuota")
    max_cost, min_cost = cur.fetchone()
    con.close()
    stats = dict(total_cost=total_cost, avg_cost=avg_cost, total_quotas=total_quotas,
                 top_provider=top_provider, top_provider_cost=top_provider_cost,
                 top_dc=top_dc, top_dc_count=top_dc_count,
                 top_server_provider=top_server_provider, top_server_count=top_server_count,
                 top_year=top_year, top_year_cost=top_year_cost,
                 top_spec=top_spec, top_spec_count=top_spec_count,
                 max_cost=max_cost, min_cost=min_cost)
    return render_template('index.html', stats=stats, pw_error=pw_error)

if __name__ == '__main__':
    app.run(debug=False)






