import json
import re
import urllib
import xml.etree.ElementTree as ET

def parse_attributes():
    schema = urllib.urlopen('http://www.w3.org/MarkUp/SCHEMA/aria-attributes-1.xsd')
    tree = ET.parse(schema)

    for node in tree.iter():
        node.tag = re.sub(r'{.*}', r'', node.tag)

    type_map = {
        'states': 'state',
        'props': 'property'
    }
    properties = {}
    groups = tree.getroot().findall('attributeGroup')
    print groups
    for group in groups:
        print(group.get('name'))
        name_match = re.match(r'ARIA\.(\w+)\.attrib', group.get('name'))
        if not name_match:
            continue
        group_type = name_match.group(1)
        print group_type
        if group_type not in type_map:
            continue
        type = type_map[group_type]
        for child in group:
            name = re.sub(r'aria-', r'', child.attrib['name'])
            property = {}
            property['type'] = type
            if 'type' in child.attrib:
                valueType = re.sub(r'xs:', r'', child.attrib['type'])
                if valueType == 'IDREF':
                    property['valueType'] = 'idref'
                elif valueType == 'IDREFS':
                    property['valueType'] = 'idref_list'
                else:
                    property['valueType'] = valueType
            else:
                type_spec = child.findall('simpleType')[0]
                restriction_spec = type_spec.findall('restriction')[0]
                base = restriction_spec.attrib['base']
                if base == 'xs:NMTOKENS':
                    property['valueType'] = 'token_list'
                elif base == 'xs:NMTOKEN':
                    property['valueType'] = 'token'
                else:
                    raise Exception('Unknown value type: %s' % base)
                values = []
                for value_type in restriction_spec:
                    values.append(value_type.get('value'))
                property['values'] = values
            if 'default' in child.attrib:
                property['defaultValue'] = child.attrib['default']
            properties[name] = property
    return json.dumps(properties, sort_keys=True, indent=4, separators=(',', ': '))



if __name__ == "__main__":
    attributes_json = parse_attributes()
    constants_file = open('src/js/Constants.js', 'r')
    new_constants_file = open('src/js/Constants.new.js', 'w')
    in_autogen_block = False
    for line in constants_file:
        if not in_autogen_block:
            new_constants_file.write('%s' % line)
        if re.match(r'// BEGIN ARIA_PROPERTIES_AUTOGENERATED', line):
            in_autogen_block = True
        if re.match(r'// END ARIA_PROPERTIES_AUTOGENERATED', line):
            break
    new_constants_file.write('/** @type {Object.<string, Object>} */\n')
    new_constants_file.write('axs.constants.ARIA_PROPERTIES = %s;\n' % attributes_json)
    new_constants_file.write('// END ARIA_PROPERTIES_AUTOGENERATED\n')
    for line in constants_file:
        new_constants_file.write('%s' % line)
