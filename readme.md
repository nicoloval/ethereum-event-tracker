First, you need to save the following files in the correct directory:
- the abi json file of the contract goes in the folder `./abi/`, the file name is the contract name. 
    e.g.
    ```
    ./abi/stETH.json
    ```
- the event in solidity format goes into the `./event/` folder, the name is the contract name, dash, event name.
    e.g.
    ```
    ./event/stETH-Transer.sol
    ```

You can now call the script, using the following command:
```
python event_tracker.py -contract-name stETH --contract-address 0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84 --event-name Transfer
```
- contract address is the address of the contract. in the example is stETH token contract address.
- additional arguments can be passed to limit the range of blocks to search. Default behaviour is from block 0 to last block in the node.
    ```
    python event_tracker.py --contract-name stETH --contract-address 0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84 --event-name Transfer --from-block 18006105 --recent-block 18006110
    ```
- an additional boolean option can be set to firce the wscript to append to an existing output file. The script will automatically start form the last block recorded on the output.

The output is saved in the folder `./output`, in a csv following the naming convention `./output/{contract_name}-{event_name}.csv`.