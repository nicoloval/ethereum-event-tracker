# Requirements

Use the following command to install all the packages from `requirements.txt`:
```
pip install -r requirements.txt
```

# Configuration
You have one configuration file: `.env` which tracks:
- the global vairbales to define the abi and events directories, as well as the output directory.
    - `OUTPUT`
    - `ABI`
    - `EVENT`
- the chain id and the rpc connection are defined endpoint, as additional information the user may want to keep secret (e.g. the OPENAI api key). 

An example file is provided in `env.example`.


# How to Use it

First, you need to save the following files in the correct directory:
- the abi json file of the contract, which goes in the folder `OUTPUT=./abi/`, the file name is the contract name. 
    e.g.
    ```
    ./abi/stETH.json
    ```
- the event in solidity format, which goes into the `EVENT=./event/` folder, the name is the contract name, dash, event name.
    e.g.
    ```
    ./event/stETH-Transer.sol
    ```

You can now call the script, using the following command:
```
python parallel_event_tracker.py -contract-name stETH --contract-address 0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84 --event-name Transfer
```
- The `--contract-name`, `--contract-address`, and `--event-name` arguments are required.
    - contract address is the address of the contract. In the example is stETH token contract address.
- additional arguments can be passed to limit the range of blocks to search. Default behaviour is from block 0 to last block in the node.
    ```
    python event_tracker.py --contract-name stETH --contract-address 0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84 --event-name Transfer --from-block 18006105 --to-block 18006110
    ```
- an additional boolean option `--append` can be set to force the script to append to an existing output file. The script will automatically start from the last block recorded on the output.
- you can also define the number of cores to use with the option `--cores`
- You can also specify the block range using `--from-block` and `--recent-block` to limit the search range.
- Use the `--append` flag to append to existing output files.
- The `--cores` argument allows you to specify the number of CPU cores to allocate for the subprocesses, which controls the level of parallelism. Default is 4.

The output is saved in the folder `./output`, in a collection of `.parquet` files following the naming convention `{OUTPUT}/{config.contract_name}-{config.event_name}-{step}-{toblock}.parquet`. A parquet file is created every 500,000 blocks in the range given when running the script.

Logs are created in `./logs`.
