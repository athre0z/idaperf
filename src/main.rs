use regex::Regex;
use std::collections::HashMap;
use std::env;
use std::io::{self, prelude::*};

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord)]
struct Symbol {
    ctr_tot: u64,
    ctr_top: u64,
    name: String,
}

fn main() -> io::Result<()> {
    let args: Vec<_> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} module-filter-string", args[0]);
        return Ok(());
    }

    let filter_str = &args[1];
    let stdin = io::stdin();
    let stdin = stdin.lock();
    let mut symbols = HashMap::new();
    let regex = Regex::new(r"\s{4,}([a-fA-F0-9]{8,16}) (.*?) \(([^\)]*?\))$").unwrap();
    let mut is_top_of_stack = false;

    for line in stdin.lines() {
        if let Some(grps) = regex.captures(&line?) {
            let (addr, sym, module) = (&grps[1], &grps[2], &grps[3]);

            if sym.starts_with("??") || !module.contains(filter_str) {
                continue;
            }

            let record = symbols
                .entry(u64::from_str_radix(addr, 16).unwrap())
                .or_insert_with(|| Symbol {
                    name: sym.to_owned(),
                    ctr_tot: 0,
                    ctr_top: 0,
                });

            record.ctr_tot += 1;

            if is_top_of_stack {
                record.ctr_top += 1;
                is_top_of_stack = false;
            }
        } else {
            is_top_of_stack = true;
        }
    }

    for (addr, sym) in &symbols {
        println!("0x{:X},{},{},{}", addr, sym.ctr_tot, sym.ctr_top, sym.name);
    }

    if symbols.is_empty() {
        eprintln!("warn: no records processed");
    }

    Ok(())
}
