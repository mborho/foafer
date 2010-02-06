/** 
 FOAFer
 Copyright (C) 2003, 2010, Martin Borho <martin@borho.net>
 
 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.
 
 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/
var API_ENDPOINT = "/api";
var LOAD_ICON = '<img src="/static/images/loader.gif" border="0" style="margin-bottom:-5px;"/>'
var INFO_ICON = '<img src="/static/images/magnify.gif" border="0" />';

function showInfoIcon() {
    document.write(INFO_ICON)
}

function getRSS(element,url,mode) {

    if($('#'+element).html() == '') {
        $('#link_'+element).html('<span id="loader_'+element+'" stye="display:none;">'+LOAD_ICON+'</span>');

        $.getJSON(API_ENDPOINT+'?mode='+mode+'&amp;url='+url+'&amp;num=5&amp;out=json',
            function(data) {
                    $('#link_'+element).html(INFO_ICON);
                    if(data.entries && data.entries.length > 0) {
                        $('#'+element).append('<b><small>Latest Entries:</small></b>:<br/>');
                        $.each(data.entries, function(i,item){
                            var link = '<a href="'+item.link+'" target="_blank">'+item.title+'</a><br/>';
                            $('#'+element).append(link);
                            if ( i == 3 ) {
                                $('#'+element).append('<a href="'+url+'" target="_blank">...more</a><br/>');
                                return false;
                            }
                        });
                    } else {
                        $('#'+element).append('<b><small>No Data for could be retrieved!</small></b>');
                    }
                    $('#'+element).slideToggle('slow');
                }
            );
    } else {
        $('#'+element).slideToggle('slow');
    }
}

function setImgSize(elem) {
	var iWidth = elem.width;
	if(iWidth > 200) {
		var ratio = elem.height/iWidth;
		elem.width=200;
		elem.height=200*ratio;
	}
}

function addUrlInput() {
    console.info($('url_form'));
    try {
        $('#url_form').append('<input type="text" name="url" value="" size="70" /><br/>');
    } catch(e) {};
}
