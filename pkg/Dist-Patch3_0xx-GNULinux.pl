#!/usr/bin/perl
#
# Copyright 2008 Pascal Giard <evilynux@gmail.com>
#
# Create patch for FoFiX from a list of source:destination
# Look at ../Makefile for a usage example.
use strict;
use warnings;
use File::Path;
use File::Remove qw(remove);
use File::NCopy;
use File::Find;

my (@src, @dest, @tuple, @svndirs);
my $dir = $ARGV[0] or die "Need destination directory!";
my $list = "Dist-MegaLight-GNULinux.lst";
#Dist-Patch3_0xx-GNULinux.lst";
my $cwd = ( $0 =~ /(^.*\/)[^\/]+$/ ) ? $1 : "./";

sub delsvn {
  return unless ( $File::Find::name =~ /\.svn$/ );
  push @svndirs, $File::Find::name;
}

open(FH, "$cwd$list") or die $!;
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

for(my $i = 0; $i < scalar(@src); $i++ ) {
  mkpath("$dir/$dest[$i]") unless ( -e "$dir/$dest[$i]" );
  $cp->copy("$src[$i]", "$dir/$dest[$i]")
    or die "Copy of $src[$i] to $dir/$dest[$i] failed: $!";
}

chdir $dir;
remove( \1, qw{
               src/*.pyc src/*.pyo src/*.bat
               src/midi/*.pyc src/midi/*.pyo } ) or die $!;
find({ wanted => \&delsvn, no_chdir => 1 }, ".");
remove( \1, @svndirs ) or die $! if( scalar(@svndirs) > 0 );
chdir "..";

__END__
