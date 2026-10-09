package com.keyboardsounds.app

data class SoundProfile(
    val id: String,
    val displayName: String,
    val folderName: String
) {
    companion object {
        val ALL = listOf(
            SoundProfile("cream", "NovelKeys Cream", "Cream"),
            SoundProfile("cherry_red", "Cherry MX Red", "Cherry MX Red"),
            SoundProfile("cherry_brown", "Cherry MX Brown", "Cherry MX Brown"),
            SoundProfile("holy_panda", "Holy Panda", "Holy Panda"),
            SoundProfile("kailh_white", "Kailh Box White", "Kailh Box White"),
            SoundProfile("tealios", "Tealios V2", "Tealios V2"),
            SoundProfile("buckling", "Buckling Spring", "Buckling Spring"),
            SoundProfile("cardboard", "Cardboard", "Cardboard")
        )

        fun findByFolderName(folder: String): SoundProfile {
            return ALL.find { it.folderName.equals(folder, ignoreCase = true) } ?: ALL.first()
        }
    }
}
