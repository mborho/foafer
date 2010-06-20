import re

def getRssContainer(target, source_type=''):
        div_id = re.sub('[^\w]','_',target)
        ajax_div = ' <a href="" onclick="try {getRSS(\'%s\',\'%s\',\'auto\');} catch(e) {};return false;" id="link_%s" title="click for latest entries">' % (div_id, target, div_id)
        ajax_div += '<script type="text/javascript">showInfoIcon();</script></a>'
        ajax_div += '<div class="api_target" id="'+div_id+'"></div>'
        return ajax_div
        
        
def account_block(name, account, url=None, rss=None):
    ''' acount block, icon has to be png '''
    if url is None:
        url = account.get('homepage','')
    out = '<a href="%s" title="%s">' % (url, account.get('homepage','') )
    out += '<img src="static/images/%s.png" border="0" alt="%s" /></a>' % (name, account.get('homepage',''))
    out += '<i>%s</i>' % account.get('name','')
    if rss:
        out += getRssContainer(rss)
    out +='<br/>'
    return out