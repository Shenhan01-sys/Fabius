// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title LockRegistry (C-A, M3)
///
/// Pra-registrasi yang tidak bisa digeser: "spesifikasi bot X (atau kunci ambang X) sudah ada pada blok ini". Selama ini pra-registrasi
/// ber-sha bergantung pada cap waktu commit git dan, untuk kunci ambang v1, pada satu baris DecisionAnchor yang dipetakan sebagai ABSTAIN (F-D74).
/// Kontrak ini tempat yang semestinya: `lockedAt` = cap waktu blok, ditulis sekali, tidak bisa diubah atau dihapus siapa pun, termasuk kami.
///
/// Aturan yang ditegakkan kontrak:
///  1. Satu kunci per (pengunci, botId, specSha). Mengubah satu angka spesifikasi = specSha lain = kunci baru dengan jam baru ("pivot = kunci baru").
///  2. Kunci milik ALAMAT yang menguncinya: orang lain bisa mengunci botId yang sama, tetapi itu kunci mereka (id berbeda), bukan kunci kami -
///     jadi tidak ada yang bisa "mendahului" lalu mengklaim jam kunci kami.
///  3. Nilai nol ditolak (botId/specSha nol = tidak ada yang dikunci).
///
/// Yang TIDAK dibuktikan: bahwa spesifikasinya bagus, menguntungkan, atau dijalankan dengan jujur. Ia hanya membuktikan keberadaan dan urutan waktu.
contract LockRegistry {
    struct Lock {
        address locker;
        uint64 lockedAt;
        bytes32 botId;
        bytes32 specSha;
    }

    mapping(bytes32 => Lock) private _locks;
    bytes32[] private _ids;

    /// `uri` hanya penunjuk (mis. jalur berkas spesifikasi di repo pada commit tertentu); tidak disimpan, tidak ikut id.
    event Locked(bytes32 indexed id, address indexed locker, bytes32 indexed botId, bytes32 specSha, uint64 lockedAt, string uri);

    error ZeroValue();
    error AlreadyLocked(bytes32 id);

    function lockId(address locker, bytes32 botId, bytes32 specSha) public pure returns (bytes32) {
        return keccak256(abi.encode(locker, botId, specSha));
    }

    function lock(bytes32 botId, bytes32 specSha, string calldata uri) external returns (bytes32 id) {
        if (botId == bytes32(0) || specSha == bytes32(0)) revert ZeroValue();
        id = lockId(msg.sender, botId, specSha);
        if (_locks[id].locker != address(0)) revert AlreadyLocked(id);
        _locks[id] = Lock({locker: msg.sender, lockedAt: uint64(block.timestamp), botId: botId, specSha: specSha});
        _ids.push(id);
        emit Locked(id, msg.sender, botId, specSha, uint64(block.timestamp), uri);
    }

    /// 0 = tidak pernah dikunci oleh `locker`.
    function lockedAt(address locker, bytes32 botId, bytes32 specSha) external view returns (uint64) {
        return _locks[lockId(locker, botId, specSha)].lockedAt;
    }

    function getLock(bytes32 id) external view returns (Lock memory) {
        return _locks[id];
    }

    function lockCount() external view returns (uint256) {
        return _ids.length;
    }

    function lockIdAt(uint256 index) external view returns (bytes32) {
        return _ids[index];
    }
}
