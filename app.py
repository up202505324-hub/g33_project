# -*- coding: utf-8 -*-
"""
Created on Mon May 18 09:57:15 2026

@author: gabri
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import datetime
import os
import sys
import sqlite3
import pandas as pd
import plotly.graph_objects as go
 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
from classes.provider import Provider
from classes.datacenter import Datacenter
from classes.serverspec import ServerSpec
from classes.server import Server
from classes.usagequota import UsageQuota
 
app = Flask(__name__)
app.secret_key = 'cloud_secret_key_2026'
 
DB_PATH = 'data/cloud.db'
 
def load_all():
    Provider.read(DB_PATH)
    Datacenter.read(DB_PATH)
    ServerSpec.read(DB_PATH)
    Server.read(DB_PATH)
    UsageQuota.read(DB_PATH)
 
load_all()

COLORS = {
    'accent':  '#00d4ff',
    'accent2': '#7c3aed',
    'success': '#10b981',
    'warning': '#f59e0b',
    'card':    '#1a2235',
    'border':  '#1e3a5f',
    'text':    '#e2e8f0',
}
 
def base_layout(**kwargs):
    layout = dict(
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['card'],
        font=dict(family='Syne, sans-serif', color=COLORS['text']),
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(gridcolor=COLORS['border'], zerolinecolor=COLORS['border']),
        yaxis=dict(gridcolor=COLORS['border'], zerolinecolor=COLORS['border']),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color=COLORS['text'])),
    )
    layout.update(kwargs)
    return layout
 
def get_chart_above_avg():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT p.name as fornecedor, SUM(u.cost) as custo_total
        FROM UsageQuota u JOIN Provider p ON u.provider_id = p.id
        GROUP BY p.id, p.name ORDER BY custo_total DESC
    """, con)
    con.close()
    media = df['custo_total'].mean()
    df_above = df[df['custo_total'] > media].head(20).sort_values('custo_total')
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_above['custo_total'], y=df_above['fornecedor'], orientation='h',
        marker=dict(color=df_above['custo_total'],
                    colorscale=[[0, COLORS['accent2']], [1, COLORS['accent']]]),
        hovertemplate='<b>%{y}</b><br>Total: €%{x:,.0f}<extra></extra>',
    ))
    fig.add_vline(x=media, line_dash='dash', line_color=COLORS['warning'],
                  annotation_text=f'Média: €{media:,.0f}',
                  annotation_font_color=COLORS['warning'])
    fig.update_layout(**base_layout(height=500, showlegend=False,
                                    xaxis_title='Custo Total (€)'))
    return fig.to_html(full_html=False, include_plotlyjs='cdn',
                       config={'displayModeBar': False})
 
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
        marker=dict(color=COLORS['accent2']),
        hovertemplate='<b>%{y}</b><br>Quotas: %{x}<extra></extra>',
    ))
    fig.update_layout(**base_layout(height=380, showlegend=False,
                                    xaxis_title='Número de Quotas de Utilização'))
    return fig.to_html(full_html=False, include_plotlyjs=False,
                       config={'displayModeBar': False})
 
def get_chart_servers():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT p.name as fornecedor, COUNT(*) as servidores
        FROM Server s JOIN Provider p ON s.provider_id = p.id
        GROUP BY p.id, p.name ORDER BY servidores DESC LIMIT 10
    """, con)
    con.close()
    df = df.sort_values('servidores')
    fig = go.Figure(go.Bar(
        x=df['servidores'], y=df['fornecedor'], orientation='h',
        marker=dict(color=COLORS['success']),
        hovertemplate='<b>%{y}</b><br>Servidores: %{x}<extra></extra>',
    ))
    fig.update_layout(**base_layout(height=380, showlegend=False,
                                    xaxis_title='Número de Servidores'))
    return fig.to_html(full_html=False, include_plotlyjs=False,
                       config={'displayModeBar': False})
 
def get_chart_yearly():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT substr(usage_date,1,4) as ano,
               SUM(cost) as custo_total, AVG(cost) as custo_medio
        FROM UsageQuota GROUP BY ano ORDER BY ano
    """, con)
    con.close()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['ano'], y=df['custo_total'], name='Custo Total (€)',
        marker=dict(color=COLORS['accent'], opacity=0.8),
        hovertemplate='<b>%{x}</b><br>Total: €%{y:,.0f}<extra></extra>',
        yaxis='y1',
    ))
    fig.add_trace(go.Scatter(
        x=df['ano'], y=df['custo_medio'], name='Custo Médio (€)',
        mode='lines+markers',
        line=dict(color=COLORS['warning'], width=2),
        marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>Média: €%{y:,.0f}<extra></extra>',
        yaxis='y2',
    ))
    fig.update_layout(**base_layout(
        height=380,
        xaxis_title='Ano',
        yaxis=dict(title='Custo Total (€)', gridcolor=COLORS['border'],
                   zerolinecolor=COLORS['border']),
        yaxis2=dict(title='Custo Médio (€)', overlaying='y', side='right',
                    gridcolor='rgba(0,0,0,0)', zerolinecolor='rgba(0,0,0,0)',
                    color=COLORS['text']),
    ))
    return fig.to_html(full_html=False, include_plotlyjs=False,
                       config={'displayModeBar': False})

@app.route('/')
def index():
    stats = {
        'providers':   len(Provider.lst),
        'datacenters': len(Datacenter.lst),
        'serverspecs': len(ServerSpec.lst),
        'servers':     len(Server.lst),
        'usagequotas': len(UsageQuota.lst),
    }
    return render_template('index.html', stats=stats)
 
@app.route('/charts')
def charts():
    return render_template('charts.html',
                           chart_above_avg=get_chart_above_avg(),
                           chart_top_dc=get_chart_top_dc(),
                           chart_servers=get_chart_servers(),
                           chart_yearly=get_chart_yearly())

@app.route('/providers')
def providers():
    items = [Provider.obj[k] for k in Provider.lst]
    return render_template('list.html', items=items, cls='Provider',
                           des=Provider.des, att=Provider.att)
 
@app.route('/providers/new', methods=['GET', 'POST'])
def provider_new():
    if request.method == 'POST':
        try:
            Provider(0, request.form['name'], request.form['creation_date'])
            Provider.insert(max(Provider.lst))
            flash('Provider criado com sucesso!', 'success')
            return redirect(url_for('providers'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    return render_template('form.html', cls='Provider', obj=None,
                           fields=[('name', 'Nome', 'text'),
                                   ('creation_date', 'Data de Criação', 'date')])
 
@app.route('/providers/<int:id>/edit', methods=['GET', 'POST'])
def provider_edit(id):
    obj = Provider.obj.get(id)
    if not obj:
        flash('Provider não encontrado.', 'error')
        return redirect(url_for('providers'))
    if request.method == 'POST':
        try:
            obj.name = request.form['name']
            obj.creation_date = request.form['creation_date']
            Provider.update(id)
            flash('Provider atualizado com sucesso!', 'success')
            return redirect(url_for('providers'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    fields = [('name', 'Nome', 'text'), ('creation_date', 'Data de Criação', 'date')]
    values = {'name': obj.name, 'creation_date': obj.creation_date}
    return render_template('form.html', cls='Provider', obj=obj,
                           fields=fields, values=values)
 
@app.route('/providers/<int:id>/delete', methods=['POST'])
def provider_delete(id):
    try:
        Provider.remove(id)
        flash('Provider eliminado.', 'success')
    except Exception as e:
        flash(f'Erro: {e}', 'error')
    return redirect(url_for('providers'))

@app.route('/datacenters')
def datacenters():
    items = [Datacenter.obj[k] for k in Datacenter.lst]
    return render_template('list.html', items=items, cls='Datacenter',
                           des=Datacenter.des, att=Datacenter.att)
 
@app.route('/datacenters/new', methods=['GET', 'POST'])
def datacenter_new():
    if request.method == 'POST':
        try:
            Datacenter(0, request.form['title'], request.form['category'])
            Datacenter.insert(max(Datacenter.lst))
            flash('Datacenter criado com sucesso!', 'success')
            return redirect(url_for('datacenters'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    return render_template('form.html', cls='Datacenter', obj=None,
                           fields=[('title', 'Nome', 'text'),
                                   ('category', 'Categoria', 'text')])
 
@app.route('/datacenters/<int:id>/edit', methods=['GET', 'POST'])
def datacenter_edit(id):
    obj = Datacenter.obj.get(id)
    if not obj:
        flash('Datacenter não encontrado.', 'error')
        return redirect(url_for('datacenters'))
    if request.method == 'POST':
        try:
            obj.title = request.form['title']
            obj.category = request.form['category']
            Datacenter.update(id)
            flash('Datacenter atualizado com sucesso!', 'success')
            return redirect(url_for('datacenters'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    fields = [('title', 'Nome', 'text'), ('category', 'Categoria', 'text')]
    values = {'title': obj.title, 'category': obj.category}
    return render_template('form.html', cls='Datacenter', obj=obj,
                           fields=fields, values=values)
 
@app.route('/datacenters/<int:id>/delete', methods=['POST'])
def datacenter_delete(id):
    try:
        Datacenter.remove(id)
        flash('Datacenter eliminado.', 'success')
    except Exception as e:
        flash(f'Erro: {e}', 'error')
    return redirect(url_for('datacenters'))

@app.route('/serverspecs')
def serverspecs():
    items = [ServerSpec.obj[k] for k in ServerSpec.lst]
    return render_template('list.html', items=items, cls='ServerSpec',
                           des=ServerSpec.des, att=ServerSpec.att)
 
@app.route('/serverspecs/new', methods=['GET', 'POST'])
def serverspec_new():
    if request.method == 'POST':
        try:
            ServerSpec(0, request.form['ram_gb'], request.form['cpu_cores'],
                       request.form['operating_system'], request.form['storage_gb'])
            ServerSpec.insert(max(ServerSpec.lst))
            flash('ServerSpec criada com sucesso!', 'success')
            return redirect(url_for('serverspecs'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    fields = [('ram_gb', 'RAM (GB)', 'number'), ('cpu_cores', 'Núcleos CPU', 'number'),
              ('operating_system', 'Sistema Operativo', 'text'),
              ('storage_gb', 'Armazenamento (GB)', 'number')]
    return render_template('form.html', cls='ServerSpec', obj=None, fields=fields)
 
@app.route('/serverspecs/<int:id>/edit', methods=['GET', 'POST'])
def serverspec_edit(id):
    obj = ServerSpec.obj.get(id)
    if not obj:
        flash('ServerSpec não encontrada.', 'error')
        return redirect(url_for('serverspecs'))
    if request.method == 'POST':
        try:
            obj.ram_gb = request.form['ram_gb']
            obj.cpu_cores = request.form['cpu_cores']
            obj.operating_system = request.form['operating_system']
            obj.storage_gb = request.form['storage_gb']
            ServerSpec.update(id)
            flash('ServerSpec atualizada com sucesso!', 'success')
            return redirect(url_for('serverspecs'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    fields = [('ram_gb', 'RAM (GB)', 'number'), ('cpu_cores', 'Núcleos CPU', 'number'),
              ('operating_system', 'Sistema Operativo', 'text'),
              ('storage_gb', 'Armazenamento (GB)', 'number')]
    values = {'ram_gb': obj.ram_gb, 'cpu_cores': obj.cpu_cores,
              'operating_system': obj.operating_system, 'storage_gb': obj.storage_gb}
    return render_template('form.html', cls='ServerSpec', obj=obj,
                           fields=fields, values=values)
 
@app.route('/serverspecs/<int:id>/delete', methods=['POST'])
def serverspec_delete(id):
    try:
        ServerSpec.remove(id)
        flash('ServerSpec eliminada.', 'success')
    except Exception as e:
        flash(f'Erro: {e}', 'error')
    return redirect(url_for('serverspecs'))

@app.route('/servers')
def servers():
    items = [Server.obj[k] for k in Server.lst]
    providers_map = {k: Provider.obj[k].name for k in Provider.lst}
    specs_map = {k: f"{ServerSpec.obj[k].ram_gb}GB / {ServerSpec.obj[k].cpu_cores} núcleos"
                 for k in ServerSpec.lst}
    return render_template('list.html', items=items, cls='Server',
                           des=Server.des, att=Server.att,
                           providers_map=providers_map, specs_map=specs_map)
 
@app.route('/servers/new', methods=['GET', 'POST'])
def server_new():
    if request.method == 'POST':
        try:
            Server(0, request.form['extra_info'],
                   int(request.form['provider_id']), int(request.form['spec_id']))
            Server.insert(max(Server.lst))
            flash('Server criado com sucesso!', 'success')
            return redirect(url_for('servers'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    providers = [Provider.obj[k] for k in Provider.lst]
    specs = [ServerSpec.obj[k] for k in ServerSpec.lst]
    return render_template('form_server.html', cls='Server', obj=None,
                           providers=providers, specs=specs)
 
@app.route('/servers/<int:id>/edit', methods=['GET', 'POST'])
def server_edit(id):
    obj = Server.obj.get(id)
    if not obj:
        flash('Server não encontrado.', 'error')
        return redirect(url_for('servers'))
    if request.method == 'POST':
        try:
            obj.extra_info = request.form['extra_info']
            obj.provider_id = int(request.form['provider_id'])
            obj.spec_id = int(request.form['spec_id'])
            Server.update(id)
            flash('Server atualizado com sucesso!', 'success')
            return redirect(url_for('servers'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    providers = [Provider.obj[k] for k in Provider.lst]
    specs = [ServerSpec.obj[k] for k in ServerSpec.lst]
    return render_template('form_server.html', cls='Server', obj=obj,
                           providers=providers, specs=specs)
 
@app.route('/servers/<int:id>/delete', methods=['POST'])
def server_delete(id):
    try:
        Server.remove(id)
        flash('Server eliminado.', 'success')
    except Exception as e:
        flash(f'Erro: {e}', 'error')
    return redirect(url_for('servers'))

@app.route('/usagequotas')
def usagequotas():
    items = [UsageQuota.obj[k] for k in UsageQuota.lst]
    providers_map = {k: Provider.obj[k].name for k in Provider.lst}
    datacenters_map = {k: Datacenter.obj[k].title for k in Datacenter.lst}
    return render_template('list.html', items=items, cls='UsageQuota',
                           des=UsageQuota.des, att=UsageQuota.att,
                           providers_map=providers_map, datacenters_map=datacenters_map)
 
@app.route('/usagequotas/new', methods=['GET', 'POST'])
def usagequota_new():
    if request.method == 'POST':
        try:
            UsageQuota(0, int(request.form['provider_id']),
                       int(request.form['datacenter_id']),
                       request.form['usage_date'], float(request.form['cost']))
            UsageQuota.insert(max(UsageQuota.lst))
            flash('UsageQuota criada com sucesso!', 'success')
            return redirect(url_for('usagequotas'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    providers = [Provider.obj[k] for k in Provider.lst]
    datacenters = [Datacenter.obj[k] for k in Datacenter.lst]
    return render_template('form_usagequota.html', cls='UsageQuota', obj=None,
                           providers=providers, datacenters=datacenters)
 
@app.route('/usagequotas/<int:id>/edit', methods=['GET', 'POST'])
def usagequota_edit(id):
    obj = UsageQuota.obj.get(id)
    if not obj:
        flash('UsageQuota não encontrada.', 'error')
        return redirect(url_for('usagequotas'))
    if request.method == 'POST':
        try:
            obj.provider_id = int(request.form['provider_id'])
            obj.datacenter_id = int(request.form['datacenter_id'])
            obj.usage_date = request.form['usage_date']
            obj.cost = float(request.form['cost'])
            UsageQuota.update(id)
            flash('UsageQuota atualizada com sucesso!', 'success')
            return redirect(url_for('usagequotas'))
        except Exception as e:
            flash(f'Erro: {e}', 'error')
    providers = [Provider.obj[k] for k in Provider.lst]
    datacenters = [Datacenter.obj[k] for k in Datacenter.lst]
    return render_template('form_usagequota.html', cls='UsageQuota', obj=obj,
                           providers=providers, datacenters=datacenters)
 
@app.route('/usagequotas/<int:id>/delete', methods=['POST'])
def usagequota_delete(id):
    try:
        UsageQuota.remove(id)
        flash('UsageQuota eliminada.', 'success')
    except Exception as e:
        flash(f'Erro: {e}', 'error')
    return redirect(url_for('usagequotas'))

if __name__ == '__main__':
    app.run(debug=False)