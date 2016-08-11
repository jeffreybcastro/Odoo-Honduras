# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import base64
from openerp.osv import osv
from openerp.report import report_sxw
from common_report_header import common_report_header
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime,timedelta
from openerp.tools.translate import _
import xlsxwriter
class account_balance(report_sxw.rml_parse, common_report_header):
    _name = 'report.account.account.balance'

    def __init__(self, cr, uid, name, context=None):
        super(account_balance, self).__init__(cr, uid, name, context=context)
        self.sum_debit = 0.00
        self.currency=0
        self.sum_credit = 0.00
        self.date_lst = []
        self.date_lst_string = ''
        self.result_acc = []
        self.result_acc2=[]
        self.result_acc3=[]
        self.usuario=self.pool.get('res.users').browse(cr,uid,uid,context=context).name
        self.fecha=(datetime.today()-relativedelta(hours=6)).strftime("%Y-%m-%d %H:%M")
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'sum_debit': self._sum_debit,
            'sum_credit': self._sum_credit,
            'get_fiscalyear':self._get_fiscalyear,
            'get_filter': self._get_filter,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period ,
            'get_account': self._get_account,
            'get_journal': self._get_journal,
            'get_start_date':self._get_start_date,
            'get_end_date':self._get_end_date,
            'get_target_move': self._get_target_move,
            'usuario':self.usuario,
            'fecha':self.fecha,
        })
        self.context = context
        
        
    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        if (data['model'] == 'ir.ui.menu'):
            new_ids = 'chart_account_id' in data['form'] and [data['form']['chart_account_id']] or []
            objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
        return super(account_balance, self).set_context(objects, data, new_ids, report_type=report_type)

    def _get_account(self, data):
        if data['model']=='account.account':
            return self.pool.get('account.account').browse(self.cr, self.uid, data['form']['id']).company_id.name
        return super(account_balance ,self)._get_account(data)

    def lines(self, form, ids=None, done=None):
        def _process_child(accounts, disp_acc, parent,result_acc2,flag2):
                account_rec = [acct for acct in accounts if acct['id']==parent][0]                
                currency_obj = self.pool.get('res.currency')
                acc_id = self.pool.get('account.account').browse(self.cr, self.uid, account_rec['id'])
                currency = acc_id.currency_id and acc_id.currency_id or acc_id.company_id.currency_id
                if form['filtrar_moneda']:
                    res = {
                        'id': account_rec['id'],
                        'type': account_rec['type'],
                        'code': account_rec['code'],
                        'name': account_rec['name'],
                        'level': account_rec['level'],
                        'debit': account_rec['debit_currency'],
                        'credit': account_rec['credit_currency'],
                        'balance': account_rec['balance_currency'],
                        'parent_id': account_rec['parent_id'],
                        'bal_type': '',
                        'saldo_ini':0.00,
                        'currency_id':self.currency
                    }
                    self.sum_debit += account_rec['debit_currency']
                    self.sum_credit += account_rec['credit_currency']
                else:
                    res = {
                        'id': account_rec['id'],
                        'type': account_rec['type'],
                        'code': account_rec['code'],
                        'name': account_rec['name'],
                        'level': account_rec['level'],
                        'debit': account_rec['debit'],
                        'credit': account_rec['credit'],
                        'balance': account_rec['balance'],
                        'parent_id': account_rec['parent_id'],
                        'bal_type': '',
                        'saldo_ini':0.00,
                    }

                    self.sum_debit += account_rec['debit']
                    self.sum_credit += account_rec['credit']


                flag=False
                if disp_acc == 'movement':
                    for dic in result_acc2:
                        if res['code']==dic['code']:
                            if not currency_obj.is_zero(self.cr, self.uid, currency, dic['balance']):
                                flag=True
                                break
                    if form['filtrar_cuenta']:
                        if res['code']==form['cuenta_inicial']:
                            flag2=True
                        if flag2 or res['code']==form['cuenta_final']:
                            if not currency_obj.is_zero(self.cr, self.uid, currency, res['credit']) or not currency_obj.is_zero(self.cr, self.uid, currency, res['debit']) or not currency_obj.is_zero(self.cr, self.uid, currency, res['balance']) or flag:
                                self.result_acc.append(res)
                    else:
                        if not currency_obj.is_zero(self.cr, self.uid, currency, res['credit']) or not currency_obj.is_zero(self.cr, self.uid, currency, res['debit']) or not currency_obj.is_zero(self.cr, self.uid, currency, res['balance']) or flag:
                                self.result_acc.append(res)

                elif disp_acc == 'not_zero':
                    if not currency_obj.is_zero(self.cr, self.uid, currency, res['balance']):
                        self.result_acc.append(res)
                else:
                    self.result_acc.append(res)

                if res['code']==form['cuenta_final']:
                    flag2=False
                if account_rec['child_id']:
                    for child in account_rec['child_id']:
                        _process_child(accounts,disp_acc,child,result_acc2,flag2)

        def _process_child2(accounts, disp_acc, parent):
                account_rec = [acct for acct in accounts if acct['id']==parent][0]
                currency_obj = self.pool.get('res.currency')
                acc_id = self.pool.get('account.account').browse(self.cr, self.uid, account_rec['id'])
                currency = acc_id.currency_id and acc_id.currency_id or acc_id.company_id.currency_id
                if form['filtrar_moneda']:
                    res = {
                        'id': account_rec['id'],
                        'type': account_rec['type'],
                        'code': account_rec['code'],
                        'name': account_rec['name'],
                        'level': account_rec['level'],
                        'debit': account_rec['debit_currency'],
                        'credit': account_rec['credit_currency'],
                        'balance': account_rec['balance_currency'],
                        'currency_id':self.currency
                    }
                else:
                    res = {
                        'id': account_rec['id'],
                        'type': account_rec['type'],
                        'code': account_rec['code'],
                        'name': account_rec['name'],
                        'level': account_rec['level'],
                        'debit': account_rec['debit'],
                        'credit': account_rec['credit'],
                        'balance': account_rec['balance'],
                    }
                self.result_acc2.append(res)
                if account_rec['child_id']:
                    for child in account_rec['child_id']:
                        _process_child2(accounts,disp_acc,child)

        def _process_child3(accounts, disp_acc, parent):
                account_rec = [acct for acct in accounts if acct['id']==parent][0]
                currency_obj = self.pool.get('res.currency')
                acc_id = self.pool.get('account.account').browse(self.cr, self.uid, account_rec['id'])
                currency = acc_id.currency_id and acc_id.currency_id or acc_id.company_id.currency_id
                if form['filtrar_moneda']:                
                    res = {
                        'id': account_rec['id'],
                        'type': account_rec['type'],
                        'code': account_rec['code'],
                        'name': account_rec['name'],
                        'level': account_rec['level'],
                        'debit': account_rec['debit_currency'],
                        'credit': account_rec['credit_currency'],
                        'balance': account_rec['balance_currency'],
                        'currency_id':self.currency
                    }

                else:
                    res = {
                        'id': account_rec['id'],
                        'type': account_rec['type'],
                        'code': account_rec['code'],
                        'name': account_rec['name'],
                        'level': account_rec['level'],
                        'debit': account_rec['debit'],
                        'credit': account_rec['credit'],
                        'balance': account_rec['balance'],
                    }
                self.result_acc3.append(res)
                if account_rec['child_id']:
                    for child in account_rec['child_id']:
                        _process_child3(accounts,disp_acc,child)


        obj_account = self.pool.get('account.account')
        if not ids:
            ids = self.ids
        if not ids:
            return []
        if not done:
            done={}
        ctx = self.context.copy()
        ctx2=self.context.copy()
        ctx3=self.context.copy()
        fiscal_ids=self.pool.get('account.fiscalyear').search(self.cr,self.uid,[])
        obj_fiscal=self.pool.get('account.fiscalyear').browse(self.cr,self.uid,fiscal_ids,ctx)
        obj_periodo_fiscal=self.pool.get('account.period').search(self.cr,self.uid,[('fiscalyear_id','=',form['fiscalyear_id']),('special','=',True)])
        obj_periodo=self.pool.get('account.period').search(self.cr,self.uid,[('fiscalyear_id','=',form['fiscalyear_id'])])
             

        if len(obj_periodo_fiscal)>1:
            raise osv.except_osv(_('Data Incorrecta'),
                    _('Existe mas de un periodo fiscal como periodo de apertura'))
        obj_periodo_browse=self.pool.get('account.period').browse(self.cr,self.uid,obj_periodo_fiscal,ctx)
        fecha_inicio=obj_periodo_browse.date_start
        fecha_fin=obj_periodo_browse.date_stop 
        date_start=''
        for mfecha in obj_fiscal:
            date_start=mfecha.date_start
            for mfecha2 in obj_fiscal:
                if mfecha.date_start>mfecha2.date_start:
                    date_start=mfecha2.date_start
            break

        ctx['fiscalyear'] = form['fiscalyear_id']
        if form['filter']=='filter_no':
             ctx['period_from'] = obj_periodo_fiscal[0]
             ctx['period_to'] = obj_periodo[len(obj_periodo)-1]
             ctx['state'] = form['target_move']
             ctx['currency_id']=3

        if form['filter'] == 'filter_date':
            fecha=datetime.strptime(form['date_from'], "%Y-%m-%d")
            fecha= fecha+timedelta(days=-1)
            fecha=datetime.strftime(fecha,"%Y-%m-%d")
        if form['filter'] == 'filter_period':
            ctx['period_from'] = form['period_from']
            ctx['period_to'] = form['period_to']
        
        elif form['filter'] == 'filter_date':
            ctx['date_from'] = form['date_from']
            ctx['date_to'] =  form['date_to']
        ctx['state'] = form['target_move']
#-----------------------------------------------------------------------------------------------------------------
        flags=False
        flags2=False      
        if form['filter']=='filter_no':
             flags2=True
             ctx2['fiscalyear'] = form['fiscalyear_id']
             ctx2['period_from'] = obj_periodo_fiscal[0]
             ctx2['period_to'] = obj_periodo_fiscal[0]
             ctx2['state'] = form['target_move']
        else:
            ctx2['fiscalyear'] = form['fiscalyear_id'] 
            if form['filter'] == 'filter_period':
                obj_fiscal=self.pool.get('account.fiscalyear').browse(self.cr,self.uid,form['fiscalyear_id'],ctx)
                for fiscal in obj_fiscal:
                    for periodos in fiscal.period_ids:
                        array.append(periodos.date_start)
                
                for periodo in self.pool.get('account.period').browse(self.cr,self.uid,form['period_from'],ctx):
                    periodo_final_fecha=periodo.date_start
                date_p=datetime.strptime(periodo_final_fecha, "%Y-%m-%d") - timedelta(days=1)
           
                ctx2['date_from'] = array[0]
                if periodo_final_fecha==fecha_inicio:
                    flags=True
                else:
                    flags=False
                ctx2['date_to'] = datetime.strftime(date_p,"%Y-%m-%d")
                ctx3['fiscalyear'] = form['fiscalyear_id'] 
                ctx3['state'] = form['target_move']
                ctx3['period_from'] = obj_periodo_fiscal[0]
                ctx3['period_to'] = obj_periodo_fiscal[0]
            
            elif form['filter'] == 'filter_date':
                ctx3['fiscalyear'] = form['fiscalyear_id'] 
                ctx3['state'] = form['target_move']
                ctx3['period_from'] = obj_periodo_fiscal[0]
                ctx3['period_to'] = obj_periodo_fiscal[0]

                obj_fiscal=self.pool.get('account.fiscalyear').browse(self.cr,self.uid,form['fiscalyear_id'],ctx)
                ctx2['date_from'] = obj_fiscal.date_start
                date_a=datetime.strptime(form['date_from'], "%Y-%m-%d") - timedelta(days=1)
                ctx2['date_to'] =  datetime.strftime(date_a,"%Y-%m-%d")
            ctx2['state'] = form['target_move']
#-----------------------------------------------------------------------------------------------------------------
        if form['filtrar_moneda']:
            curr=form['currency'][0]
            obj_account_ids_currency=self.pool.get('account.account').search(self.cr,self.uid,[('currency_id','=',curr)])
            arreglotemp=obj_account_ids_currency
            arreglox=[]
            while len(arreglotemp)!=0:
                arreglox.append(arreglotemp[0])
                child_ids = obj_account._get_children_and_consol(self.cr, self.uid,arreglotemp[0], ctx)
                for valor in child_ids:
                    if valor in arreglotemp:
                        arreglotemp.remove(valor)
            ids=arreglox
            parents = arreglox
        else:
            parents=ids
        child_ids = obj_account._get_children_and_consol(self.cr, self.uid,ids, ctx)
        if child_ids:
            ids = child_ids
        if form['filtrar_moneda']:
            
            self.currency=self.pool.get('res.currency').browse(self.cr,self.uid, form['currency'][0],context=None)
            accounts = obj_account.read(self.cr, self.uid,ids, ['type','code','name','debit_currency','credit_currency','balance_currency','parent_id','level','child_id','currency_id'], ctx)
            accounts2 = obj_account.read(self.cr, self.uid, ids, ['type','code','name','debit_currency','credit_currency','balance_currency','parent_id','level','child_id','currency_id'], ctx2)
            accounts3 = obj_account.read(self.cr, self.uid, ids, ['type','code','name','debit_currency','credit_currency','balance_currency','parent_id','level','child_id','currency_id'], ctx3)

        else:
            accounts = obj_account.read(self.cr, self.uid,ids, ['type','code','name','debit','credit','balance','parent_id','level','child_id','currency_id'], ctx)
            accounts2 = obj_account.read(self.cr, self.uid, ids, ['type','code','name','debit','credit','balance','parent_id','level','child_id','currency_id'], ctx2)
            accounts3 = obj_account.read(self.cr, self.uid, ids, ['type','code','name','debit','credit','balance','parent_id','level','child_id','currency_id'], ctx3)
        for parent in parents:
                if parent in done:
                    continue
                done[parent] = 1
#------------------------------------------------------------------------------------------------------------------
                
                a=parent   
                rango=0     
                #revsar si el ultimo es parent
                _process_child2(accounts2,form['display_account'],parent)
                for i,x in enumerate(self.result_acc2):
                    if x['id']==a:
                        rango=i
                
                        
                #suma del periodo de apertura en caso de ser diferente de el rango del periodo de apertura ya que de lo contrario esta incluido    
                if form['date_from']==fecha_inicio or flags:
                    _process_child3(accounts3,form['display_account'],parent)
                    #borrar de resultacc2
                    #for a in self.result_acc2:
                       
                    
                    for a in range(rango,len(self.result_acc2)):
                        for b in self.result_acc3:
                            if  self.result_acc2[a]['code']==b['code']:
                                self.result_acc2[a]['debit']+=b['debit']
                                self.result_acc2[a]['credit']+=b['credit']
                                self.result_acc2[a]['balance']+=b['balance']
                   
                        
#-------------------------------------------------------------------------------------------------------------------
                _process_child(accounts,form['display_account'],parent,self.result_acc2,flag2=False)
       
        for x in self.result_acc:
            for y in self.result_acc2:
                if x['code']==y['code']:
                    if y['balance']:
                            if (form['date_from']!=fecha_inicio or flags) and flags2==False:
                                x['saldo_ini']=y['balance']
                                x['balance']=y['balance']+x['debit']-x['credit']
                                break
                            if form['date_from']==fecha_inicio  or flags or flags2:
                                x['saldo_ini']=y['balance']
                                x['debit']-=y['debit']
                                x['credit']-=y['credit']
                                x['balance']=y['balance']+x['debit']-x['credit']
                            
                    else:
                        x['balance']=x['debit']-x['credit']
                    break
                else:
                    x['saldo_ini']=0.00
        if form['filtrar_cuenta']:
            temp=0
            for arreglo in self.result_acc:
                
                if form['cuenta_inicial']==arreglo['code']:
                    temp=0
                if form['cuenta_final']==arreglo['code']:
                    temp=1
            if temp==0:
                return []
         

        return self.result_acc


class report_trialbalance(osv.AbstractModel):
    _name = 'report.account.report_trialbalance'
    _inherit = 'report.abstract_report'
    _template = 'account.report_trialbalance'
    _wrapped_report_class = account_balance

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: