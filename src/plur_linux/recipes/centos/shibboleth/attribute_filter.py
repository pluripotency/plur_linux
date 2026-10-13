from plur import base_shell


def create_contents(sp_server_name):
    contents = """<?xml version="1.0" encoding="UTF-8"?>
<AttributeFilterPolicyGroup id="ShibbolethFilterPolicy"
        xmlns="urn:mace:shibboleth:2.0:afp"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="urn:mace:shibboleth:2.0:afp http://shibboleth.net/schema/idp/shibboleth-afp.xsd">

    <AttributeFilterPolicy id="requester_url">
        <PolicyRequirementRule xsi:type="Requester" value="requester_url" />
        <AttributeRule attributeID="eduPersonTargetedID">
            <PermitValueRule xsi:type="ANY" />
        </AttributeRule>
    </AttributeFilterPolicy>
</AttributeFilterPolicyGroup>""".replace('requester_url', "https://%s/shibboleth" % sp_server_name)
    return contents


def configure(sp_server_name):
    def deco(session):
        file_path = '$SHIB_HOME/conf/attribute-filter.xml'
        base_shell.create_backup(session, file_path)
        base_shell.here_doc(session, file_path, create_contents(sp_server_name).split('\r\n|\n'))
    return deco
