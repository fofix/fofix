#!/usr/bin/perl
#
# Copyright 2008 Pascal Giard <evilynux@gmail.com>
#
# Create patch for FoFiX from a list of source:destination
# Look at ../Makefile for a usage example.
use strict;
use warnings;
use Getopt::Long;
use File::Path;
use File::Remove qw(remove);
use File::NCopy;
use File::Find;

use vars qw(%opt @src @dest @tuple @svndirs);
my $cwd = ( $0 =~ /(^.*\/)[^\/]+$/ ) ? $1 : "./";

GetOptions( "dest=s"   => \$opt{'dir'},
	    "list=s"    => \$opt{'list'} );

die "Need destination directory!" unless( defined $opt{'dir'} );
$opt{'list'} = "Dist-MegaLight-GNULinux.lst" unless( defined $opt{'list'} );

sub delsvn {
  return unless ( $File::Find::name =~ /\.svn$/ );
  push @svndirs, $File::Find::name;
}

open(FH, "$opt{'list'}") or die $!;
while( <FH> ) {
  chop();
  next if( /^$/ );
  @tuple = split( /:/, $_);
  push @src, $tuple[0];
  push @dest, $tuple[1];
}
close FH;

my $cp = File::NCopy->new(recursive => 1,
                          force_write => 1,
                          follow_links => 1);

mkpath("$opt{'dir'}");
for(my $i = 0; $i < scalar(@src); $i++ ) {
  mkpath("$opt{'dir'}/$dest[$i]") unless ( -e "$opt{'dir'}/$dest[$i]" );
  $cp->copy("$src[$i]", "$opt{'dir'}/$dest[$i]")
    or die "Copy of $src[$i] to $opt{'dir'}/$dest[$i] failed: $!";
}

chdir $opt{'dir'};
remove( \1, qw{
               src/*.pyc src/*.pyo src/*.bat
               src/midi/*.pyc src/midi/*.pyo } ) or die $!;
find({ wanted => \&delsvn, no_chdir => 1 }, ".");
remove( \1, @svndirs ) or die $! if( scalar(@svndirs) > 0 );
chdir "..";

__END__
