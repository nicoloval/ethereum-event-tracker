# Requirements

Use the following command to install all the packages from `requirements.txt`:
```
pip install -r requirements.txt
```

# Configuration
You have one configuration file: `.env` which tracks:
- the global vairbales to define the abi and events locations are defined, as well as the output folder.
    - `OUTPUT`
    - `ABI`
    - `EVENT`
- the chain id and the rpc connection are defined, as additional information the user may want to keep secret (e.g. the OPENAI api key). 

An example file is provided in `.env.example`.


# How to Use it

First, you need to save the following files in the correct directory:
- the abi json file of the contract goes in the folder `OUTPUT=./abi/`, the file name is the contract name. 
    e.g.
    ```
    ./abi/stETH.json
    ```
- the event in solidity format goes into the `EVENT=./event/` folder, the name is the contract name, dash, event name.
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
- an additional boolean option can be set to force the script to append to an existing output file. The script will automatically start from the last block recorded on the output.

# Using parallel_event_tracker.py

The `parallel_event_tracker.py` script allows you to track events in parallel by dividing the block range into smaller segments and processing them concurrently. This can significantly speed up the event tracking process.

To use the script, run the following command:

```
python parallel_event_tracker.py --contract-name stETH --contract-address 0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84 --event-name Transfer
```

- The `--contract-name`, `--contract-address`, and `--event-name` arguments are required, similar to `event_tracker.py`.
- You can also specify the block range using `--from-block` and `--recent-block` to limit the search range.
- Use the `--append` flag to append to existing output files.
- The `--cores` argument allows you to specify the number of CPU cores to allocate for the subprocesses, which controls the level of parallelism.

Example with additional arguments:

```
python parallel_event_tracker.py --contract-name stETH --contract-address 0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84 --event-name Transfer --from-block 18006105 --recent-block 18006110 --cores 4
```

This command will track the `Transfer` event from block `18006105` to `18006110` using up to 4 CPU cores for parallel processing.

The output is saved in the folder `./output`, in a `.parquet` files following the naming convention `{OUTPUT}/{config.contract_name}-{config.event_name}-{step}-{toblock}.parquet`. A file is created every 500,000 blocks.
