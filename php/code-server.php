<?php

/* Generates permutations of sets of three alpha-numeric characters. 
 * I am not a PHP developer and have never written any more than what's
 * here, so please have mercy on my soul. */

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


function randomize($file) {
	$lines = file($file);
	$lines = pc_array_shuffle($lines);
	$fh = fopen($file, 'w') or die("Can't open file");
	foreach($lines as $line) {
		fwrite($fh, $line);
	}
	fclose($fh);
}
	

generate('codes.txt');
randomize('codes.txt');


?>
