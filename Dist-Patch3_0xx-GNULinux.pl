#!/usr/bin/perl -w
#
# Copyright 2008 Pascal Giard <evilynux@gmail.com>
#
# Create patch for FoFiX from a list of source:destination
#
use strict;
use File::Copy::Recursive qw(rcopy);
use File::Remove qw(remove);

my $list = "Dist-Patch3_0xx-GNULinux.lst";
my (@src, @dest, @tuple);
my $dir = $ARGV[0] or die "Need destination directory!";

open(FH, $list) or die $!;
while( <FH> ) {
  chop();
  next if( /^$/ );
  @tuple = split( /:/, $_);
  push @src, $tuple[0];
  push @dest, $tuple[1];
}
close FH;

for(my $i = 0; $i < scalar(@src); $i++ ) {
  rcopy($src[$i], "$dir/$dest[$i]") or die "Copy failed for $src[$i]: $!";
}

chdir $dir;
remove( \1, qw{.svn */.svn */*/.svn
               src/*.pyc src/*.pyo src/*.bat
               src/midi/*.pyc src/midi/*.pyo } ) or die $!;
chdir "..";

__END__
