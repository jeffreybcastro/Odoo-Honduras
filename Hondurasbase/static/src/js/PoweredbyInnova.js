
document.getElementById('web.menu_secondary').innerHTML = '
            <a class="oe_logo" t-att-href="\'/web/?debug\' if debug else \'/web\'">
                <span class="oe_logo_edit">Edit Company data</span>
                <img src=\'/web/binary/company_logo\'/>
            </a>
            <div>
                <div>
                    <div class="oe_secondary_menus_container">
                        <t t-foreach="menu_data[\'children\']" t-as="menu">
                            <div style="display: none" class="oe_secondary_menu" t-att-data-menu-parent="menu[\'id\']">
                                <t t-foreach="menu[\'children\']" t-as="menu">
                                    <div class="oe_secondary_menu_section">
                                        <t t-esc="menu[\'name\']"/>
                                    </div>
                                    <t t-call="web.menu_secondary_submenu"/>
                                </t>
                            </div>
                        </t>
                    </div>
                </div>
            </div>
            <div class="oe_footer">
                <a href="http://www.grupomacrotec.com" target="_blank"><span>Macrotec</span></a>
            </div>'
;
