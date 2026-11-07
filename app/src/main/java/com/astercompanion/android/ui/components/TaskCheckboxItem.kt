package com.astercompanion.android.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material3.Divider
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.astercompanion.android.model.CompanionTask
import com.astercompanion.android.ui.theme.AsterColors
import com.astercompanion.android.ui.theme.AsterTheme

/**
 * Custom rounded checkbox matching the Today screen aesthetic
 * in screenshot 56539447-5086-44aa-b0ad-b98fa9cb6a8d.png.
 */
@Composable
fun TaskCheckbox(
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    modifier: Modifier = Modifier
) {
    val checkboxShape = RoundedCornerShape(6.dp)
    val animatedBgColor by animateColorAsState(
        targetValue = if (checked) AsterColors.AmberPrimary else Color.Transparent,
        label = "taskCheckboxBg"
    )
    val animatedBorderColor by animateColorAsState(
        targetValue = if (checked) AsterColors.AmberPrimary else AsterColors.TextSecondary,
        label = "taskCheckboxBorder"
    )

    Box(
        modifier = modifier
            .size(22.dp)
            .clip(checkboxShape)
            .background(animatedBgColor, checkboxShape)
            .border(1.5.dp, animatedBorderColor, checkboxShape)
            .clickable(
                onClick = { onCheckedChange(!checked) }
            ),
        contentAlignment = Alignment.Center
    ) {
        if (checked) {
            Icon(
                imageVector = Icons.Default.Check,
                contentDescription = "Checked",
                tint = AsterColors.TextOnAmber,
                modifier = Modifier.size(16.dp)
            )
        }
    }
}

/**
 * TaskCheckboxItem
 *
 * Implements the individual task row strictly matching screenshot 56539447-5086-44aa-b0ad-b98fa9cb6a8d.png:
 * - Rounded checkbox outline on the left.
 * - Task title (e.g. "Book dentist", "Finish budget draft", "Pick up parcel").
 * - Due timestamp/label (e.g. "Today", "Tomorrow", "This week").
 * - Trailing chevron right arrow.
 */
@Composable
fun TaskCheckboxItem(
    modifier: Modifier = Modifier,
    title: String,
    dueLabel: String,
    isChecked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    onClick: (() -> Unit)? = null
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .then(
                if (onClick != null) {
                    Modifier.clickable(onClick = onClick)
                } else {
                    Modifier
                }
            )
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Custom Rounded Checkbox
        TaskCheckbox(
            checked = isChecked,
            onCheckedChange = onCheckedChange
        )

        Spacer(modifier = Modifier.width(14.dp))

        // Task Title & Due Label
        Column(
            modifier = Modifier.weight(1f)
        ) {
            Text(
                text = title,
                color = if (isChecked) AsterColors.TextSecondary else AsterColors.TextPrimary,
                fontSize = 15.sp,
                fontWeight = FontWeight.Medium,
                textDecoration = if (isChecked) TextDecoration.LineThrough else TextDecoration.None
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = dueLabel,
                color = AsterColors.TextSecondary,
                fontSize = 13.sp,
                fontWeight = FontWeight.Normal
            )
        }

        // Trailing Chevron
        Icon(
            imageVector = Icons.Outlined.ChevronRight,
            contentDescription = "View task details",
            tint = AsterColors.TextMuted,
            modifier = Modifier.size(20.dp)
        )
    }
}

/**
 * Overload accepting domain model [CompanionTask].
 */
@Composable
fun TaskCheckboxItem(
    task: CompanionTask,
    modifier: Modifier = Modifier,
    onCheckedChange: (Boolean) -> Unit,
    onClick: (() -> Unit)? = null
) {
    TaskCheckboxItem(
        modifier = modifier,
        title = task.title,
        dueLabel = task.dueLabel,
        isChecked = task.isCompleted,
        onCheckedChange = onCheckedChange,
        onClick = onClick
    )
}

/**
 * TasksCard
 *
 * Card container wrapping multiple [TaskCheckboxItem]s with subtle dividing lines,
 * matching the "Your tasks" card on the Today screen.
 */
@Composable
fun TasksCard(
    modifier: Modifier = Modifier,
    tasks: List<CompanionTask>,
    onCheckedChange: (CompanionTask, Boolean) -> Unit,
    onTaskClick: (CompanionTask) -> Unit = {}
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = AsterColors.SurfaceCard
    ) {
        Column(modifier = Modifier.fillMaxWidth()) {
            tasks.forEachIndexed { index, task ->
                TaskCheckboxItem(
                    task = task,
                    onCheckedChange = { isChecked -> onCheckedChange(task, isChecked) },
                    onClick = { onTaskClick(task) }
                )
                if (index < tasks.lastIndex) {
                    HorizontalDivider(
                        modifier = Modifier.padding(start = 50.dp, end = 16.dp),
                        thickness = 0.8.dp,
                        color = AsterColors.BorderSubtle
                    )
                }
            }
        }
    }
}

// ==========================================
// Jetpack Compose Previews
// ==========================================

@Preview(name = "Tasks Card - Screenshot Match", showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun PreviewTasksCard() {
    AsterTheme {
        val sampleTasks = listOf(
            CompanionTask("1", "profile_aster", "Book dentist", "Today", isCompleted = false),
            CompanionTask("2", "profile_aster", "Finish budget draft", "Tomorrow", isCompleted = false),
            CompanionTask("3", "profile_aster", "Pick up parcel", "This week", isCompleted = false)
        )

        Box(modifier = Modifier.padding(16.dp)) {
            TasksCard(
                tasks = sampleTasks,
                onCheckedChange = { _, _ -> }
            )
        }
    }
}
