from django import template

register = template.Library()

@register.filter(name='replace')
def replace(value, args):
    """
    Replace occurrences of a string with another string.
    Usage: {{ value|replace:"old,new" }}
    """
    if not args or ',' not in args:
        return value
    
    old, new = args.split(',', 1)
    return str(value).replace(old, new)

@register.filter(name='format_field_name')
def format_field_name(value):
    """
    Convert field names like 'computer_type' to 'Computer Type'.
    """
    if not value:
        return value
    # Replace underscores with spaces and title case
    formatted = str(value).replace('_', ' ').title()
    # Handle special cases
    formatted = formatted.replace('Os', 'OS')
    formatted = formatted.replace('Cpu', 'CPU')
    formatted = formatted.replace('Ram', 'RAM')
    formatted = formatted.replace('Imei', 'IMEI')
    formatted = formatted.replace('Sim', 'SIM')
    formatted = formatted.replace('Ip', 'IP')
    formatted = formatted.replace('Dvr', 'DVR')
    formatted = formatted.replace('Nvr', 'NVR')
    formatted = formatted.replace('Iot', 'IoT')
    formatted = formatted.replace('Vin', 'VIN')
    formatted = formatted.replace('Usb', 'USB')
    formatted = formatted.replace('Ssd', 'SSD')
    formatted = formatted.replace('Hdd', 'HDD')
    return formatted
