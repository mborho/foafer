# 
# FOAFer
# Copyright (C) 2003, 2010, Martin Borho <martin@borho.net>
# Copyright (C) 2010, JKW, Joerg Kurt Wegner <me@joergkurtwegner.eu>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Changelog
# 2010-06-20: JKW, account_block adapted for creating brief account information
#

import re

def getRssContainer(target, source_type=''):
        div_id = re.sub('[^\w]','_',target)
        ajax_div = ' <a href="" onclick="try {getRSS(\'%s\',\'%s\',\'auto\');} catch(e) {};return false;" id="link_%s" title="click for latest entries">' % (div_id, target, div_id)
        ajax_div += '<script type="text/javascript">showInfoIcon();</script></a>'
        ajax_div += '<div class="api_target" id="'+div_id+'"></div>'
        return ajax_div
        
        
def account_block(name, account, url=None, rss=None, brief=None):
    ''' acount block, icon has to be png '''
    if url is None:
        url = account.get('homepage','')
    out = '<a href="%s" title="%s">' % (url, account.get('homepage','') )
    out += '<img src="static/images/%s.png" border="0" alt="%s" /></a>' % (name, account.get('homepage',''))
    if brief == 'true':
      if rss:
        out += '[<a href="%s" title="%s">rss</a>]' % (rss,account.get('homepage',''))
      out +=', '
    else:
      out += '<i>%s</i>' % account.get('name','')
      if rss:
          out += getRssContainer(rss)
      out +='<br/>'
    return out
    