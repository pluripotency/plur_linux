from plur import base_shell
custom_data_connector = """
    <!-- CustomDataConnector -->
    <resolver:DataConnector id="computedID" xsi:type="dc:ComputedId"
                            generatedAttributeID="computedID"
                            sourceAttributeID="%{idp.persistentId.sourceAttribute}"
                            salt="%{idp.persistentId.salt}">
        <resolver:Dependency ref="%{idp.persistentId.sourceAttribute}" />
    </resolver:DataConnector>"""


def escape_exp(s, sep="/"):
    return s.replace('!', '\!').replace(sep, '\\'+sep).replace('=', '\=').replace('(', '\(').replace(')', '\)').replace('{', '\{').replace('}', '\}').replace('[', '\[').replace(']', '\]').replace('\n', '\\n')


def escape(s, sep="/"):
    return s.replace(sep, '\\'+sep).replace("'", "\\x27").replace('\n', '\\n')


def create_custom_attribute(sp_server_name):
    custom_attribute = """    <!-- CustomAttribute -->
    <resolver:AttributeDefinition xsi:type="ad:SAML2NameID" id="eduPersonTargetedID" nameIdFormat="urn:oasis:names:tc:SAML:2.0:nameid-format:persistent" sourceAttributeID="computedID">
        <resolver:Dependency ref="computedID" />
        <resolver:AttributeEncoder xsi:type="enc:SAML1XMLObject" name="urn:oid:1.3.6.1.4.1.5923.1.1.1.10" encodeType="false" />
        <resolver:AttributeEncoder xsi:type="enc:SAML2XMLObject" name="urn:oid:1.3.6.1.4.1.5923.1.1.1.10" friendlyName="eduPersonTargetedID" encodeType="false" />
    </resolver:AttributeDefinition>
    <resolver:AttributeDefinition id="eduPersonTargetedIDLogging" xsi:type="Script" xmlns="urn:mace:shibboleth:2.0:resolver:ad">
      <!-- Dependency that provides the source attribute. -->
      <resolver:Dependency ref="computedID" />
      <resolver:Dependency ref="eduPersonPrincipalName" />
      <Script><![CDATA[
           logger = Java.type("org.slf4j.LoggerFactory").getLogger("net.shibboleth.idp.attribute");

           if (  resolutionContext.attributeRecipientID.equals("logging_target_url") ) {
               logger.info(
                       "eduPersonPrincipalName : " + eduPersonPrincipalName.getValues().get(0).getValue() 
                               + '@' + eduPersonPrincipalName.getValues().get(0).getScope()
                       + " , eduPersonTargetedID : " + computedID.getValues().get(0) 
                      );
           }
      ]]></Script>
    </resolver:AttributeDefinition>
    """.replace('logging_target_url', "https://%s/shibboleth" % sp_server_name)
    return custom_attribute


def sed_e(src, dst, exp_list):
    action = "sed -e "
    for i, exp in enumerate(exp_list):
        if i == 0:
            action += "'%s' %s " % (exp, src)
        else:
            action += "| sed -e '%s' " % exp
    action += ' > %s' % dst
    return action


def sed_s(src, dst, sep="/"):
    return sep.join([
        "s",
        src,
        dst,
        ""
    ])


def configure(sp_server_name, file_path='$SHIB_HOME/conf/attribute-resolver.xml'):
    def func(session):
        base_shell.create_backup(session, file_path)

        delete_seperator = "/" + escape_exp("^    <!-- ========================================== -->$") + "/d"
        attribute_def = sed_s(
            escape_exp("^    <!--      Attribute Definitions                 -->$"),
            escape("""    <!-- ========================================== -->
    <!--      Attribute Definitions                 -->
    <!-- ========================================== -->"""))

        data_connectors = sed_s(
            escape_exp("^    <!--      Data Connectors                       -->$"),
            escape(create_custom_attribute(sp_server_name) + """
    <!-- ========================================== -->
    <!--      Data Connectors                       -->
    <!-- ========================================== -->
""" + custom_data_connector))

        sed_action = sed_e(file_path + '.org', file_path, [
            delete_seperator,
            attribute_def,
            data_connectors
        ])
        base_shell.run(session, sed_action)

    return func


def test():
    from plur import session_wrap
    from plur import base_node
    sp_server_name = 'c7sp.r'

    @session_wrap.bash()
    def run(session=None):
        configure(sp_server_name, file_path='~/Documents/sed_test/attribute-resolver.xml')(session)
    run()


if __name__ == '__main__':
    test()
