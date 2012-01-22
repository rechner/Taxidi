<?php

/* code-server.php
 * 
 * Copyright © 2012 Zac Sturgeon (2012/01/22 22:33:14)
 * 
 * Generates permutations of sets of three alpha-numeric characters,
 * and returns a random, unique code, re-shuffling after all codes
 * are exhausted (every 16'120 runs in it's current configuration).
 * 
 * I am not a PHP developer and have never written any more than what's
 * here, so please have mercy on my soul.   The two files below should
 * be stored somewhere OUTSIDE the webserver's path somewhere which
 * the server has authority to read, write, and create these two files
 * in.  Exposing the list and index would make sequences predictable,
 * making it theoretically possible to forge parent codes. 
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301, USA.
 *     
 */
 
$index = 'codes.index'; //file to store the current line number
$codes = 'codes.txt';

function generate($file) {
	// Generate formats for ANA, NAN, and AAN (X = alpha, N = number)
	$alpha = range('A', 'Z');
	$numbers = range(0, 9);
	
	$fh = fopen($file, 'w') or die("Can't open file");
		
	foreach ($alpha as $i) {
		foreach ($numbers as $j) {
			foreach ($alpha as $k) {
				fwrite($fh, $i . $j . $k . "\n");
			}
		}
	}
	
	foreach ($numbers as $i) {
		foreach ($alpha as $j) {
			foreach ($numbers as $k) {
				fwrite($fh, $i . $j . $k . "\n");
			}
		}
	}
	
	foreach ($alpha as $i) {
		foreach ($alpha as $j) {
			foreach ($numbers as $k) {
				fwrite($fh, $i . $j . $k . "\n");
			}
		}
	}
	
	fclose($fh);
}

//shuffle function
function pc_array_shuffle($array) {
    $i = count($array);

    while(--$i) {
        $j = mt_rand(0, $i);

        if ($i != $j) {
            // swap elements
            $tmp = $array[$j];
            $array[$j] = $array[$i];
            $array[$i] = $tmp;
        }
    }

    return $array;
}

// shufle the line order of a file.
function randomize($file) {
	$lines = file($file);
	$lines = pc_array_shuffle($lines);
	$fh = fopen($file, 'w') or die("Can't open file");
	foreach($lines as $line) {
		fwrite($fh, $line);
	}
	fclose($fh);
}

function getIndex($index) {
	if ( file_exists($index) ) {
		$f = file($index);
	} else { //file doesn't exist; create it and store '1'.
		setIndex($index, '0');
		$f = array('0');
	}
	return $f[0];
}

function getRecord($codes, $line) {
	$f = file($codes) or die("Can't open codes: $codes");
	return $f[$line];
}		
	

function setIndex($index, $value) {
	$fh = fopen($index, 'w') or die("Can't open index: $index");
	fwrite($fh, $value);
	fclose($fh);
}	

// if either codes.txt or codes.index doesn't exist, generate new codes.
if ( ! file_exists($index) || ! file_exists($codes) ) {
	generate($codes);
	randomize($codes);
}


/* begin main program */

$i = getIndex($index);
$lines = count(file($codes));
	
if ( $i == $lines ) {
	// shuffle file and reset the count
	randomize($codes);
	setIndex($index, '0');
	$i = 0;
}

$read = file($codes);	// read all the codes into $read
echo $read[$i];   // output the $i-th line

$i++;	//incrament the counter and save it
setIndex($index, $i);


?>
