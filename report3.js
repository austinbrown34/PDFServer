var page = require( 'webpage' ).create(),
   system = require('system');

page.paperSize = {
  format: 'A4',
  orientation: 'portrait',
  margin: '0cm'
};

if ( system.args.length < 3 ) {
 console.log( 'Usage: report.js <some URL> <output path/filename>' );
 phantom.exit();
}

page.open( system.args[ 1 ], function( status ) {
 console.log( "Status: " + status );

 if ( status === "success" ) {
   page.render( system.args[ 2 ] );

 }
 phantom.exit();
} );
