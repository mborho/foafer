/*
 * GMapEZ -- Turn specially-marked HTML into Google Maps
 * Copyright (C) July 2005 - Oct 2006 by Chris Houser <chouser@n01se.net>
 *
 * This code is licensed under the GNU General Public License (GPL)
 *
 * If you use this code on a web page, please include on that page a
 * link to http://n01se.net/gmapez/ -- this is a request, not
 * a requirement.  Thanks.
 */

(function(){
  var startdate = new Date();

  // configuration -- if you're using your own copy of gmapez.js, you
  // may want to modify these:
  var overlaysPerStep = 25;
  var imgBase = 'http://gmapez.googlepages.com/';
  var upperImgBase = 'http://gmapez.upper.googlepages.com/';
  var shadowServer = 'http://n01se.net/shadow.cgi?src=';

  if( window.ez_preload ) {
    // we're already loaded
    return;
  }

  var _lastId = 0;
  function newId() {
    return 'ez_' + (++_lastId);
  }

  function loadfunc() {
    if( ! GBrowserIsCompatible() ) {
      if( document.getElementsByTagName ) {
        // Find all divs marked as GMapEZ
        var divs = document.getElementsByTagName( 'div' );
        for( var i = 0; i < divs.length; ++i ) {
          var div = divs[ i ];
          if( div.className.indexOf( 'GMapEZ' ) > -1 ) {
            div.innerHTML =  [
              "<div>This map cannot be displayed.  The site's key may be ",
              "incorrect, or your browser may not compatible (see if ",
              "your browser is listed ",
              '<a href="http://maps.google.com/support/bin/answer.py?answer=16532">here</a>).</div>',
              '<div class="firefoxref"><iframe src="http://pagead2.googlesyndication.com/cpa/ads?client=ca-pub-1237864095616304&amp;cpa_choice=CAAQyaj8zwEaCIwcWMzeycafKMu293M&amp;oe=UTF-8&amp;dt=1148266564041&amp;lmt=1148266562&amp;format=180x60_as_rimg&amp;output=html&amp;region=_google_cpa_region_&amp;cc=100&amp;u_h=1024&amp;u_w=1280&amp;u_ah=1050&amp;u_aw=1400&amp;u_cd=24&amp;u_tz=-240&amp;u_his=1&amp;u_java=true&amp;u_nplug=11&amp;u_nmime=133" marginwidth="0" marginheight="0" vspace="0" hspace="0" allowtransparency="true" frameborder="0" height="60" scrolling="no" width="180"></iframe></div>'
              ].join('\n');
            div.style.visibility = 'visible';
            div.style.padding = '0.3em';
            div.style.background = '#eee';
            div.style.overflow = 'auto';
          }
        }
      }
      else {
        alert( [
          'Your browser is not capable of displaying',
          'Google Maps on this page. Try using Firefox:',
          'http://getfirefox.com/' ].join('\n') );
      }
      return;
    }

    addOnUnload( GUnload );

    function getTotalOffset( elem ) {
      point = new GPoint( 0, 0 );
      while( elem ) {
        point.x += elem.offsetLeft;
        point.y += elem.offsetTop;
        //alert( elem.offsetTop + ' = ' + point.y );
        elem = elem.offsetParent;
      }
      return point;
    }

    function GSmallMapTypeControl() {
      GMapTypeControl.call( this, true );
    }
    GSmallMapTypeControl.prototype = new GMapTypeControl();
    GSmallMapTypeControl.prototype.constructor = GSmallMapTypeControl;
    window.GSmallMapTypeControl = GSmallMapTypeControl;

    var CtrlTable = {
      'GOverviewMapControl': true,
      'GLargeMapControl': true,
      'GSmallMapControl': true,
      'GSmallZoomControl': true,
      'GSmallMapTypeControl': true,
      'GMapTypeControl': true,
      'GMenuMapTypeControl': true,
      'GHierarchicalMapTypeControl': true,
      'GScaleControl': true
    };

    var MapTypeTable = {
      'G_NORMAL_MAP' : null,
      'G_SATELLITE_MAP' : null,
      'G_HYBRID_MAP' : null,
      'G_PHYSICAL_MAP' : null,
      'G_MAP_TYPE' : 'G_NORMAL_MAP',
      'G_SATELLITE_TYPE' : 'G_SATELLITE_MAP',
      'G_HYBRID_TYPE' : 'G_HYBRID_MAP'
    };

    var idmarkers = {};
    function markerForUrl( url ) {
      var matcha = /#(.*)/.exec( url );
      if( matcha )
        return idmarkers[ matcha[ 1 ] ];
      else
        return null;
    }

    // For this event handler, "this" is the clicked anchor
    function anchorClick() {
      var marker = markerForUrl( this.href );
      if( marker ) {
        if( /\bZOOM\b/.exec( this.className ) ) {
          var mapType = marker.mapType || marker.ezmap.map.getCurrentMapType();
          var zoomLevel;
          if( marker.span ) {
            zoomLevel = mapType.getSpanZoomLevel(
              marker.point, marker.span, marker.ezmap.viewsize );
          }
          else {
            zoomLevel = marker.ezmap.map.getZoom();
          }
          marker.ezmap.map.setCenter( marker.point, zoomLevel, mapType );
        }
        marker.doOpen();
        return false;
      }
      else {
        return true;
      }
    }

    function wordMap( str ) {
      var wmap = {};
      var list = str.split(' ');
      for( var j = 0; j < list.length; ++j ) {
        wmap[ list[ j ] ] = true;
      }
      return wmap;
    }

    function parseParams( str, params ) {
      var matchparam;
      for( var word in wordMap( str ) ) {
        matchparam = /^(\w+):(.*)$/.exec( word );
        if( matchparam && matchparam[1] in params ) {
          params[ matchparam[1] ] = matchparam[2];
        }
      }
      return params;
    }

    var markerOpener = {
      markers: [],
      addMarker: function( marker ) {
        this.markers.push( marker );
      },
      chainOpen: function( i ) {
        /*
         * This is a work-around for a Google Maps bug.  If I try to open
         * all the info windows at once, only the last one succeeds.
         *
         * Otherwise, it is equivalent to:
         *   for( i = 0; i < this.markers.length; ++i )
         *     this.markers[ i ].doOpen();
         */
        i = i || 0;
        if( i < this.markers.length ) {
          var onOpen = GEvent.bind(
              this.markers[ i ].ezmap.map,
              "infowindowopen",
              this,
              function(){
                GEvent.removeListener( onOpen );
                this.chainOpen( i + 1 );
              });
          this.markers[ i ].doOpen( true );
        }
        else {
          //alert('GMapEZ loadtime: ' + ( new Date() - startdate ) );
        }
      }
    };

    var laterFuncs = [];
    var lastFunc = null;
    function doNow() {
      if( laterFuncs.length > 0 ) {
        laterFuncs.shift().call();
        setTimeout( doNow, 1 );
      }
      else {
        if( lastFunc ) {
          lastFunc.call();
        }
      }
    }
    function doLater( obj, func ) {
      laterFuncs.push( function() { func.call( obj ); } );
    }

    var MiniIcon = new GIcon();
    MiniIcon.shadow = "http://labs.google.com/ridefinder/images/mm_20_shadow.png";
    MiniIcon.iconSize = new GSize(12, 20);
    MiniIcon.shadowSize = new GSize(22, 20);
    MiniIcon.iconAnchor = new GPoint(6, 20);
    MiniIcon.infoWindowAnchor = new GPoint(5, 1);

    G_DEFAULT_ICON.transparent = null;
    function EZInfoMarker( ezmap ) {
      this.ezmap = ezmap;
      this.icon = G_DEFAULT_ICON;

      this.point = null;
      this.title = null;

      this.blowup = false;
      this.tabs = [];

      this.infoZoomOffset = undefined;
      this.infoZoomLevel = undefined;
      this.infoMapType = null;
    }
    EZInfoMarker.prototype = new GMarker( new GLatLng( 0, 0 ) );
    EZInfoMarker.prototype.constructor = EZInfoMarker;

    EZInfoMarker.prototype.initialize = function( map ) {
      GMarker.call(
          this,
          this.point,
          {
            icon: this.icon,
            clickable: ( this.tabs.length > 0 || this.blowup ),
            title: this.title
          });
      GMarker.prototype.initialize.call( this, map );
    };

    EZInfoMarker.prototype.doOpen = function( autoopen ) {
      if( ! autoopen ) {
        var body = document.body || document.getElementsByTagName('body')[0];
        if( 'scrollLeft' in body ) {
          // http://www.howtocreate.co.uk/tutorials/javascript/browserwindow
          var myWidth = 0, myHeight = 0;
          if( typeof( window.innerWidth ) == 'number' ) {
            //Non-IE
            myWidth = window.innerWidth;
            myHeight = window.innerHeight;
          } else if( document.documentElement &&
              ( document.documentElement.clientWidth ||
              document.documentElement.clientHeight ) )
          {
            //IE 6+ in 'standards compliant mode'
            myWidth = document.documentElement.clientWidth;
            myHeight = document.documentElement.clientHeight;
          } else if( document.body &&
              ( document.body.clientWidth || document.body.clientHeight ) )
          {
            //IE 4 compatible
            myWidth = document.body.clientWidth;
            myHeight = document.body.clientHeight;
          }

          var mapdiv = this.ezmap.div;
          var totalOffset = getTotalOffset( mapdiv );
          if( totalOffset.x < body.scrollLeft ||
              totalOffset.x + mapdiv.offsetWidth > body.scrollLeft+myWidth ||
              totalOffset.y < body.scrollTop ||
              totalOffset.y + mapdiv.offsetHeight > body.scrollTop+myHeight)
          {
            //alert( totalOffset.x + ', ' + totalOffset.y );
            scrollTo( totalOffset.x, totalOffset.y );
          }
        }
      }

      var zoom = null;
      if( this.tabs.length > 0 ) {
        var opts = { maxWidth: this.ezmap.div.offsetWidth - 100 };
        if( this.icon ) {
          this.openInfoWindowTabs( this.tabs, opts );
        }
        else {
          // "INVISIBLE" markers are never added as overlays -- GMap2
          // knows nothing about them.
          this.ezmap.map.openInfoWindowTabs( this.point, this.tabs, opts );
        }
        for( var i = 0; i < this.tabs.length; ++i ) {
          this.setupInfoForm( this.tabs[ i ] );
        }
      }
      else if( this.blowup ) {
        if( this.infoZoomOffset != undefined )
          zoom = this.ezmap.map.getZoom() + this.infoZoomOffset;
        else if( this.infoZoomLevel != undefined )
          zoom = this.infoZoomLevel;

        if( zoom >= this.ezmap.map.getCurrentMapType().numZoomLevels )
          zoom = this.ezmap.map.getCurrentMapType().numZoomLevels - 1;
        else if( zoom < 0 )
          zoom = 0;

        this.showMapBlowup( { zoomLevel: zoom, mapType: this.infoMapType } );
      }
      else {
        this.ezmap.map.closeInfoWindow();
      }
    };

    EZInfoMarker.prototype.setupInfoForm = function( tab ) {
      var div, a;
      var tabElem = tab.contentElem;
      var classes = tabElem.className ? wordMap( tabElem.className ) : {};
      if( classes.DirectionsToHere ||
          classes.DirectionsFromHere ||
          classes.SearchNearby )
      {
        if( tab.infoFormId ) {
          div = document.getElementById( tab.infoFormId );
          div.innerHTML = '';
        }
        else {
          div = document.createElement('div');
          div.className = 'ez_infoForm';
          tab.infoFormId = div.id = newId();
          tabElem.appendChild( div );
        }
        var _this = this;
        if( classes.DirectionsToHere || classes.DirectionsFromHere ) {
          div.appendChild( document.createTextNode( 'Get directions: ' ) );
          if( classes.DirectionsToHere ) {
            a = document.createElement('a');
            a.innerHTML = 'To here';
            a.onclick = function() { _this.showForm( tab ); };
            a.href = 'javascript:void(null)';
            div.appendChild( a );
          }
          if( classes.DirectionsToHere && classes.DirectionsFromHere ) {
            div.appendChild( document.createTextNode( ' - ' ) );
          }
          if( classes.DirectionsFromHere ) {
            a = document.createElement('a');
            a.innerHTML = 'From here';
            a.onclick = function() {};
            a.href = 'javascript:void(null)';
            div.appendChild( a );
          }
          div.appendChild( document.createElement('br') );
        }
        if( classes.SearchNearby ) {
          a = document.createElement('a');
          a.innerHTML = 'Search nearby';
          a.onclick = function() {};
          a.href = 'javascript:void(null)';
          div.appendChild( a );
        }
      }
    };

    EZInfoMarker.prototype.showForm = function( tab ) {
      var div = document.getElementById( tab.infoFormId );
      div.innerHTML = '<b>Get directions:</b> To here - ';
      var a = document.createElement('a');
      a.innerHTML = 'From here';
      a.onclick = function() {};
      a.href = 'javascript:void(null)';
      div.appendChild( a );
      var x = document.createElement('div');
      x.innerHTML = 'Start address';
      div.appendChild( x );
      this.ezmap.map.getInfoWindow().reset();
    };

    function EZPolyline( color, weight, opacity ) {
      this.points = [];
      this.initialize = function( map ) {
        GPolyline.call( this, this.points, color, weight, opacity );
        GPolyline.prototype.initialize.call( this, map );
      };
    };
    EZPolyline.prototype = new GPolyline();
    EZPolyline.prototype.constructor = EZPolyline;


    function EZMap( div, classes ) {
      this.div = div;
      this.classes = classes;
      this.divData = null;

      this.map = undefined;
      this.viewsize = null;
      this.extentMarker = null;

      this.overlayList = [];

      this.loading = null;
      this.bar = null;
      this.maxstep = 0;
      this.step = 0;
      this.oi = 0;
      this.initFrame();
    }

    EZMap.prototype.logWarning = function( str ) {
      if( ! this.warningNode ) {
        this.warningVis = false;
        this.warningNode = document.createElement('ul');
        this.warningNode.className = 'warnings';
        this.div.appendChild( this.warningNode );

        var warnBtn = document.createElement('button');
        warnBtn.className = 'warnings';
        warnBtn.innerHTML = 'Warnings...';
        this.div.appendChild( warnBtn );
        var ezmap = this;
        warnBtn.onclick = function() { ezmap.toggleWarnings(); };
      }
      var li = document.createElement('li');
      li.innerHTML = str;
      this.warningNode.appendChild( li );
    };

    EZMap.prototype.toggleWarnings = function() {
      this.warningVis = ! this.warningVis;
      this.warningNode.style.display = this.warningVis ? 'block' : 'none';
    };

    EZMap.prototype.processMarkers = function( parentNode, polyline ) {
      var lastOverlay, marker, textContent, imgs;
      var matchll, matchspn, matchtype;
      for( var node = parentNode.firstChild; node; node = node.nextSibling){
        lastOverlay = this.overlayList[ this.overlayList.length - 1 ];
        switch( node.nodeName ) {
        case 'A':
          matchll = /\Wll=([-.\d]*),([-.\d]*)/.exec( node.href );
          if( matchll ) {

            marker = new EZInfoMarker( this );
            marker.title = node.getAttribute('title');
            this.overlayList.push( marker );

            if( node.id || node.name )
              idmarkers[ node.id || node.name ] = marker;

            textContent = node.innerHTML.replace( /<[^>]*>/g, '' );

            if( /\bOPEN\b/.exec( textContent ) )
              markerOpener.addMarker( marker );

            if( /\bEXTENT\b/.exec( textContent ) ) {
              marker.icon = null;
              this.extentMarker = marker;
            }

            if( /\bINVISIBLE\b/.exec( textContent ) ) {
              marker.icon = null;
            }

            marker.point = new GLatLng(
                parseFloat( matchll[1] ),
                parseFloat( matchll[2] ) );

            if( polyline ) {
              marker.icon = null;
              polyline.points.push( marker.point );
            }

            matchspn = /\Wspn=([-.\d]*),([-.\d]*)/.exec( node.href );
            if( matchspn ) {
              marker.span = new GLatLng(
                  parseFloat( matchspn[1] ),
                  parseFloat( matchspn[2] ) );
            }

            matchtype = /\Wt=(.)/.exec( node.href );
            if( matchtype ) {
              switch( matchtype[1] ) {
                case 'k': marker.mapType = G_SATELLITE_MAP; break;
                case 'h': marker.mapType = G_HYBRID_MAP; break;
                // XXX need a GMapType letter for use by ZOOM links
              }
            }

            // build icon
            imgs = node.getElementsByTagName('img')
            if( imgs.length < 1 ) {
              var matchcolor =
                  /\b(ORANGE|PURPLE|YELLOW|GREEN|BLUE|RED|AQUA|WHITE|GRAY)\b/
                  .exec( textContent );
              var matchsym =
                  /\b([0-9A-Za-z]|BLANK|HASH|DOLLAR|DOT|START|END)\b/
                  .exec( textContent );
              var matchmini = /\bMINI\b/.exec( textContent );

              if( matchcolor || matchsym || matchmini ) {
                var upper = matchsym && matchsym[0].match(/^[A-Z]$/);
                marker.icon = new GIcon( matchmini ? MiniIcon : G_DEFAULT_ICON );
                marker.icon.image = [
                  upper ? upperImgBase : imgBase,
                  matchmini ? 'mini' : 'marker',
                  '-',
                  matchcolor ? matchcolor[0] : 'ORANGE',
                  '-',
                  matchmini ? 'BLANK' : ( matchsym ? matchsym[0] : 'DOT' ),
                  upper ? '-UPPER' : '',
                  '.png' ].join('');

                marker.icon.printImage    = marker.icon.image;
                marker.icon.mozPrintImage = marker.icon.image;
              }
            }
            else {
              marker.icon = new GIcon( G_DEFAULT_ICON, imgs[ 0 ].src );
              marker.icon.printImage    = imgs[ 0 ].src;
              marker.icon.mozPrintImage = imgs[ 0 ].src;
              marker.icon.transparent = null;
              marker.icon.iconAnchor = null;
              marker.icon.infoWindowAnchor = null;

              var params = parseParams( imgs[ 0 ].className, {
                width: null, height: null,
                iconAnchor: null, infoWindowAnchor: null, imageMap: null } );

              var match;
              var width = parseInt( params.width );
              var height = parseInt( params.height );
              marker.icon.iconSize = new GSize( width, height );

              if( params.iconAnchor ) {
                match = /(\d+),(\d+)/.exec( params.iconAnchor );
                if( match ) {
                  marker.icon.iconAnchor = new GPoint(
                    parseInt( match[1] ),
                    parseInt( match[2] ) );
                }
              }
              if( marker.icon.iconAnchor === null ) {
                marker.icon.iconAnchor = new GPoint(
                  Math.round( width / 2 ),
                  Math.max( 1, height - 2 ) );
              }

              if( params.infoWindowAnchor ) {
                match = /(\d+),(\d+)/.exec( params.infoWindowAnchor );
                if( match ) {
                  marker.icon.infoWindowAnchor = new GPoint(
                    parseInt( match[1] ),
                    parseInt( match[2] ) );
                }
              }
              if( marker.icon.infoWindowAnchor === null ) {
                marker.icon.infoWindowAnchor = new GPoint(
                  Math.round( width / 2 ),
                  0 );
              }

              if( params.imageMap ) {
                marker.icon.imageMap = [];
                var parts = params.imageMap.split(/\s*,\s*/);
                for( var i = 0; i < parts.length; ++i ) {
                  marker.icon.imageMap.push( parseInt( parts[ i ] ) );
                }
                //alert( marker.icon.imageMap );
              }

              if( imgs.length > 1 ) {
                marker.icon.shadow = imgs[ 1 ].src;
                params = parseParams( imgs[ 1 ].className, { width:0, height:0 });
                marker.icon.shadowSize = new GSize( params.width, params.height);
              }
              else {
                marker.icon.shadow = shadowServer + imgs[ 0 ].src;
                marker.icon.shadowSize = new GSize(
                    Math.floor( width + height * 0.55 ), height );
              }

              if( imgs.length > 2 ) {
                marker.icon.transparent = imgs[ 2 ].src;
              }
              if( imgs.length > 3 ) {
                marker.icon.printImage = imgs[ 3 ].src;
              }
              if( imgs.length > 4 ) {
                marker.icon.printShadow = imgs[ 4 ].src;
              }
              if( imgs.length > 5 ) {
                marker.icon.mozPrintShadow = imgs[ 5 ].src;
              }
            }
          }
          else {
            this.logWarning( "No ll param for marker [" + node.innerHTML +
              ":" + (node.id || node.name) + "]" );
          }
          break;

        case 'DIV':
          if( ! lastOverlay ) {
            this.logWarning( "div block given before any markers" );
            continue;
          }
          else {
            var infoClasses = wordMap( node.className );
            if( 'GMapEZ' in infoClasses ) {
              // infoWindow blowup
              // XXX replace this with a nested map to allow for use
              // in tabs?
              lastOverlay.blowup = true;
              var matchzoom = /ZOOMLEVEL([-+=]?)(\d+)/.exec( node.innerHTML );
              if( matchzoom ) {
                var num = parseInt( matchzoom[ 2 ] );
                if( matchzoom[ 1 ] == '-' )
                  lastOverlay.infoZoomOffset = num;
                else if( matchzoom[ 1 ] == '+' )
                  lastOverlay.infoZoomOffset = - num;
                else
                  lastOverlay.infoZoomLevel = num;
              }

              for( typeName in MapTypeTable ) {
                if( typeName in infoClasses ) {
                  if( MapTypeTable[ typeName ] ) {
                    lastOverlay.infoMapType = window[ MapTypeTable[ typeName ] ];
                  }
                  else {
                    lastOverlay.infoMapType = window[ typeName ];
                  }
                  break;
                }
              }
            }
            else {
              // XXX remove title attribute from div node?
              lastOverlay.tabs.push(
                  new GInfoWindowTab( node.getAttribute('title'), node ));
            }
          }
          break;

        case 'LI':
          this.processMarkers( node, polyline );
          break;

        case 'OL':
          var params = parseParams( node.className,
              { color: null, weight: null, opacity: null } );
          if( params.color && ! /^#[0-9a-zA-Z]{6}$/.exec( params.color ) )
            this.logWarning( 'Polyline color should be a 6-digit' +
                ' hex color like "#123abc", not "' + params.color + '"' );
          if( params.weight != null ) {
            var w = parseInt( params.weight );
            if( w < 1 || isNaN( w ) )
              this.logWarning( 'Polyline weight should be an' +
                  ' interger above 0, not "' + params.weight + '"' );
            params.weight = w;
          }
          if( params.opacity ) {
            var o = parseFloat( params.opacity );
            if( o < 0 || o > 1 || isNaN( o ) )
              this.logWarning( 'Polyline opacity should be ' +
                  ' between 0 and 1, not "' + params.opacity + '"' );
            params.opacity = o;
          }
          var newline = new EZPolyline(
              params.color,
              params.weight,
              params.opacity );
          this.overlayList.push( newline );
          this.processMarkers( node, newline );
          break;

        case '#text':
        case '#comment':
          // ignore text and comments
          break;

        default:
          this.logWarning( "Unknown or misplaced node " + node.nodeName );
          break;
        }
      }
    };

    EZMap.prototype.onClick = function( overlay, point ) {
      if( overlay && overlay.doOpen ) {
        overlay.doOpen();
      }
      else if( point ) {
        this.map.closeInfoWindow();
      }
    };

    EZMap.prototype.nextStep = function( func ) {
      if( this.maxstep > 0 ) {
        this.bar.style.width = Math.round( this.step / this.maxstep * 100 ) + '%';
      }
      this.step += 1;
      doLater( this, func );
    };

    EZMap.prototype.initFrame = function() {
      this.divData = this.div;
      this.div = this.div.cloneNode( false );
      this.divData.parentNode.insertBefore( this.div, this.divData );
      this.divData.parentNode.removeChild( this.divData );
      this.div.style.visibility = 'visible';

      this.loading = document.createElement('div');
      this.loading.className = 'loadprogress';
      this.loading.style.marginTop = ( this.div.offsetHeight / 3 ) + 'px';
      this.loading.innerHTML = '<div class="box"><div class="logo"></div><div class="trough"><div class="bar"></div></div></div>';
      this.bar = this.loading.getElementsByTagName('div')[3];
      this.div.appendChild( this.loading );

      this.nextStep( this.initParse );
    };

    EZMap.prototype.initParse = function() {
      this.processMarkers( this.divData );
      this.divData = null;

      this.map = new GMap2( this.div );
      this.map.getContainer().appendChild( this.loading );

      GEvent.bind( this.map, 'click', this, this.onClick );
      if( 'ScrollWheelZoom' in this.classes ) {
        this.map.enableScrollWheelZoom();
      }

      if( ! this.extentMarker && this.overlayList.length == 1 )
        this.extentMarker = this.overlayList[ 0 ];

      // map type
      var mapType = G_NORMAL_MAP;
      if( this.extentMarker && this.extentMarker.mapType ) {
        mapType = this.extentMarker.mapType;
      }
      for( typeName in MapTypeTable ) {
        if( typeName in this.classes ) {
          if( MapTypeTable[ typeName ] ) {
            mapType = window[ MapTypeTable[ typeName ] ];
          }
          else {
            mapType = window[ typeName ];
          }
          break;
        }
      }

      // center and zoom
      this.viewsize = new GSize( this.div.offsetWidth, this.div.offsetHeight );
      var center, zoomLevel;
      if( this.extentMarker ) {
        center = this.extentMarker.point;
        if( this.extentMarker.span ) {
          zoomLevel = mapType.getSpanZoomLevel(
              center, this.extentMarker.span, this.viewsize );
        }
        else {
          zoomLevel = 10;
        }
      }
      else if( this.overlayList.length > 1 ) {
        var autoBounds;
        for( var i = 0; i < this.overlayList.length; ++i ) {
          if( this.overlayList[ i ].point ) {
            if( ! autoBounds ) {
              autoBounds = new GLatLngBounds(
                  this.overlayList[ i ].point,
                  this.overlayList[ i ].point );
            }
            else {
              autoBounds.extend( this.overlayList[ i ].point );
            }
          }
        }
        var sw = autoBounds.getSouthWest();
        var ne = autoBounds.getNorthEast();
        center = new GLatLng(
          ( sw.lat() + ne.lat() ) / 2,
          ( sw.lng() + ne.lng() ) / 2 );
        zoomLevel = mapType.getBoundsZoomLevel( autoBounds, this.viewsize);
      }
      else {
        center = new GLatLng( 41.075210, -85.130310 );
        zoomLevel = 10;
      }

      // apply center, zoom, and map type
      this.map.setCenter( center, zoomLevel, mapType );

      this.maxstep = Math.floor( this.overlayList.length / overlaysPerStep ) + 2;
      this.initOverlays();
    };

    EZMap.prototype.initOverlays = function() {
      var overlay;
      var steplimit = Math.min(this.overlayList.length, this.oi+overlaysPerStep);
      for( ; this.oi < steplimit; ++this.oi ) {
        overlay = this.overlayList[ this.oi ];
        if( overlay.points || overlay.icon )
          this.map.addOverlay( overlay );
        this.overlayList[ this.oi ] = null;
      }
      if( this.oi < this.overlayList.length )
        this.nextStep( this.initOverlays );
      else
        this.nextStep( this.initControls );
    };

    EZMap.prototype.initControls = function() {
      for( var ctrl in CtrlTable ) {
        if( ctrl in this.classes ) {
          this.map.addControl( new window[ ctrl ]() );
        }
      }

      this.nextStep( this.initLoading );
    };

    EZMap.prototype.initLoading = function() {
      this.loading.parentNode.removeChild( this.loading );
      this.loading = null;
    };

    // Find all anchor tags linking to GMapEZ markers
    var anchors = document.getElementsByTagName( 'a' );
    for( var mi = 0; mi < anchors.length; ++mi ) {
      if( ! anchors[ mi ].onclick ) {
        anchors[ mi ].onclick = anchorClick;
      }
    }

    // Find all divs marked as GMapEZ
    var divs = document.getElementsByTagName( 'div' );
    for( var i = 0; i < divs.length; ++i ) {
      var div = divs[ i ];
      var classes = wordMap( div.className );
      if( 'GMapEZ' in classes ) {
        new EZMap( div, classes );
      }
    }

    lastFunc = function() {
      // Examine current page location for a reference to a GMapEZ marker
      var marker = markerForUrl( document.location );
      if( marker )
        markerOpener.addMarker( marker );

      // Open all the markers we need to
      markerOpener.chainOpen();
    };

    doNow();
  }

  function chainWindowFunc( funcname, newfunc ) {
    var oldfunc = window[ funcname ];
    if( oldfunc ) {
      window[ funcname ] = function() { oldfunc(); newfunc(); };
    }
    else {
      window[ funcname ] = newfunc;
    }
  }

  window.addOnLoad   = function( func ) { chainWindowFunc( "onload",   func );};
  window.addOnUnload = function( func ) { chainWindowFunc( "onunload", func );};

  window.ez_preload = function() {
    if( window.G_INCOMPAT ) {
      // If the key failed to validate, cause all keys to appear valid
      // and try again.
      window.G_INCOMPAT = false;
      window.GValidateKey = function(){ return true; }
      GLoad();
    }
    addOnLoad( loadfunc );
  }

  var key = '';
  var gmapversion = '2';
  (function(){
    var metas = document.getElementsByTagName( 'meta' );
    var match;
    for( var i = 0; i < metas.length; ++i ) {
      match = /gmapkey:?(.*)/.exec( metas[ i ].name );
      if( match ) {
        if( ! match[ 1 ] ) {
          key = metas[ i ].content;
        }
        else if( (new RegExp( match[ 1 ] )).exec( window.location.href ) ) {
          key = metas[ i ].content;
          break;
        }
      }
      else if( metas[ i ].name == 'gmapversion' ) {
        gmapversion = metas[ i ].content;
      }
    }
  })();

  if( ! window.GMap2 ) {
    document.write( [
      '<script src="http://maps.google.com/maps?file=api&v='
      + gmapversion + '&key=' + key
      + '" type="text/javascript"></script>' ].join('\n') );
  }

  document.write( [
    '<script type="text/javascript">',
    '  ez_preload();',
    '</script>',

    '<style type="text/css">',
    'div.GMapEZ {',
    '  visibility: hidden;',
    '  border: 1px #888 solid;',
    '}',

    'div.GMapEZ ul.warnings {',
    '  position: absolute;',
    '  top: 0;',
    '  left: 0;',
    '  margin: 0;',
    '  padding-right: 0.5em;',
    '  padding-left: 1.5em;',
    '  display: none;',
    '  border: 1px #888 solid;',
    '  background: #fff;',
    '  z-index: 100000000;',
    '  text-align: left;',
    '  font-family: Arial;',
    '  font-size: 9pt;',
    '  overflow: auto;',
    '}',

    'div.GMapEZ button.warnings {',
    '  display: block;',
    '  position: absolute;',
    '  z-index: 100000000;',
    '  bottom: 20px;',
    '  right: 0;',
    '  color: #f00;',
    '}',

    'div.GMapEZ .firefoxref {',
    '  text-align: center;',
    '  margin: 1em;',
    '}',

    'div.GMapEZ .loadprogress {',
    '  position: relative;',
    '  z-index: 100000000;',
    '  text-align: center;',
    '}',

    'div.GMapEZ .loadprogress .box {',
    '  font-family: Arial, sans-serif;',
    '  background: #fff;',
    '  border: 1px #bbb inset;',
    '  width: 136px;',
    '  height: 45px;',
    '  margin: auto;',
    '}',

    'div.GMapEZ .loadprogress .logo {',
    '  margin: 8px;',
    '  margin-bottom: 0;',
    '  width: 120px;',
    '  height: 28px;',
    "  filter:progid:DXImageTransform.Microsoft.AlphaImageLoader(src='" +
        imgBase + "logo3.png',sizingMethod='scale');",
    '}',
    'div.GMapEZ .loadprogress .box > .logo {',
    '  position: relative;',
    '  background: url(' + imgBase + 'logo3.png) no-repeat;',
    '}',

    'div.GMapEZ .loadprogress .trough {',
    '  margin: 8px;',
    '  margin-top: -5px;',
    '  background: #ccc;',
    '  font-size: 1px;',
    '  height: 8px;',
    '  text-align: left;',
    '}',

    'div.GMapEZ .loadprogress .bar {',
    '  height: 8px;',
    '  width: 0px;',
    '  background: #55a url(' + imgBase + 'progressbar.png);',
    '}',

    'v\\:* {',
    '  behavior:url(#default#VML);',
    '}',
    '</style>'
  ].join('\n'));
})();

